
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from sqlalchemy import text  # Add this at the top of server.py if not already there

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.148.223.31/proj1part2
#
# For example, if you had username zy2431 and password 123123, then the following line would be:
#
#     DATABASEURI = "postgresql://zy2431:123123@34.148.223.31/proj1part2"
#
# Modify these with your own credentials you received from TA!
DATABASE_USERNAME = "rp3187"
DATABASE_PASSWRD = "994639"
DATABASE_HOST = "34.148.223.31"
DATABASEURI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWRD}@{DATABASE_HOST}/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
with engine.connect() as conn:
	create_table_command = """
	CREATE TABLE IF NOT EXISTS test (
		id serial,
		name text
	)
	"""
	res = conn.execute(text(create_table_command))
	insert_table_command = """INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace')"""
	res = conn.execute(text(insert_table_command))
	# you need to commit for create, insert, update queries to reflect
	conn.commit()


@app.before_request
def before_request():
	"""
	This function is run at the beginning of every web request 
	(every time you enter an address in the web browser).
	We use it to setup a database connection that can be used throughout the request.

	The variable g is globally accessible.
	"""
	try:
		g.conn = engine.connect()
	except:
		print("uh oh, problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	"""
	At the end of the web request, this makes sure to close the database connection.
	If you don't, the database could run out of memory!
	"""
	try:
		g.conn.close()
	except Exception as e:
		pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
	"""
	request is a special object that Flask provides to access web request information:

	request.method:   "GET" or "POST"
	request.form:     if the browser submitted a form, this contains the data in the form
	request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

	See its API: https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data
	"""

	# DEBUG: this is debugging code to see what request looks like
	print(request.args)


	#
	# example of a database query
	#
	select_query = "SELECT name from test"
	cursor = g.conn.execute(text(select_query))
	names = []
	for result in cursor:
		names.append(result[0])
	cursor.close()

	#
	# Flask uses Jinja templates, which is an extension to HTML where you can
	# pass data to a template and dynamically generate HTML based on the data
	# (you can think of it as simple PHP)
	# documentation: https://realpython.com/primer-on-jinja-templating/
	#
	# You can see an example template in templates/index.html
	#
	# context are the variables that are passed to the template.
	# for example, "data" key in the context variable defined below will be 
	# accessible as a variable in index.html:
	#
	#     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
	#     <div>{{data}}</div>
	#     
	#     # creates a <div> tag for each element in data
	#     # will print: 
	#     #
	#     #   <div>grace hopper</div>
	#     #   <div>alan turing</div>
	#     #   <div>ada lovelace</div>
	#     #
	#     {% for n in data %}
	#     <div>{{n}}</div>
	#     {% endfor %}
	#
	context = dict(data = names)


	#
	# render_template looks in the templates/ folder for files.
	# for example, the below file reads template/index.html
	#
	return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/another')
def another():
	return render_template("another.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
    # accessing form inputs from user
    name = request.form['name']

    # passing params in for each variable into query
    conn=g.conn
    params = {}
    params["new_name"] = name
    conn.execute(text('INSERT INTO test(name) VALUES (:new_name)'), params)
    conn.commit()
    return redirect('/')


@app.route('/login')
def login():
	abort(401)
	this_is_never_executed()


if __name__ == "__main__":
	import click

	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8111, type=int)
	def run(debug, threaded, host, port):
		"""
		This function handles command line parameters.
		Run the server using:

			python server.py

		Show the help text using:

			python server.py --help

		"""

		HOST, PORT = host, port
		print("running on %s:%d" % (HOST, PORT))
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)



# Here are the routes to the given pages 


@app.route("/books")
# This is the first simple query connected to books.html
def books():
    print("Executing Books List")
    try:
        #combined_rating is essentially the ISBN rating 
        conn = g.conn
        books_qry = text("SELECT bookid, book_title, isbn, combined_rating FROM books;")
        print(f"Executing Qry {books_qry}")
        result = conn.execute(books_qry)
        books = result.fetchall()
        return render_template("books.html", books=books)
    except Exception as e:
        #Used to throw an error 
        return f"Error: {e}"




@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    print("Executing Add Books")
    if request.method == "POST":
        b_title = request.form["book_title"]
        b_isbn = request.form["isbn"]
        b_combined_rating = request.form.get("combined_rating", None)
        b_author_id = request.form["author_id"]
        b_genre_id = request.form["genre_id"]

        # Insert into the Books table
        conn = g.conn
        result = conn.execute(text("""
            INSERT INTO books (book_title, isbn, combined_rating)
            VALUES (:title, :isbn, :rating)
            RETURNING bookid
        """), {"title": b_title, "isbn": b_isbn, "rating": b_combined_rating})

        new_book_id = result.fetchone()[0]
        print(f"Inserted new Book, BookId - {new_book_id}")
        # This is a subquery that is used to make sure that book.html and author.html are linked. 
        conn.execute(text("""
            INSERT INTO book_authors (bookid, authorid)
            VALUES (:bookid, :authorid)
        """), {"bookid": new_book_id, "authorid": b_author_id})

        # Links the book to genre
        print("Added Book Authors Relation")
        conn.execute(text("""
            INSERT INTO bookgenres (bookid, genreid)
            VALUES (:bookid, :genreid)
        """), {"bookid": new_book_id, "genreid": b_genre_id})
        print("Added Book Generes Relation")
        conn.commit()
        return redirect("/books")

    # fetch the authhor and genre
    authors = g.conn.execute(text("SELECT authorid, name FROM authors")).fetchall()
    genres = g.conn.execute(text("SELECT genreid, genrename FROM genres")).fetchall()
    return render_template("add_book.html", authors=authors, genres=genres)

#connects to the users.html file 
@app.route("/users")
def users():
    print("Executing Users")
    try:
        conn = g.conn
        users_qry = text("SELECT userid, username, user_email, preferences FROM users;")
        print(f"Executing Qry {users_qry}")
        result = conn.execute(users_qry)
        users = result.fetchall()
        return render_template("users.html", users=users)
    except Exception as e:
        return f"Error: {e}"


@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    print("Executing Add Users")
    if request.method == "POST":
        user = request.form["username"]
        e_mail = request.form["email"]
        pref = request.form["preferences"]
        #method used to add new users
        try:
            conn = g.conn
            qry = text("INSERT INTO users (username, user_email, preferences) VALUES (:username, :email, :preferences)")
            conn.execute(qry,
                {"username": user, "email": e_mail, "preferences": pref}
            )
            g.conn.commit()
            return redirect("/users")
        except Exception as e:
            return f"Error adding user: {e}"
        #This error is thrown when there is an error adding users
    return render_template("add_user.html")


#implimented reviews
@app.route("/reviews")
def reviews():
    print("Executing Reviews")#debugging
    try:
        review_query = text("""
            SELECT re.reviewid, u.username, b.book_title, re.com_content, re.timestamp
            FROM reviews re
            JOIN users u ON re.userid = u.userid
            JOIN books b ON re.bookid = b.bookid
            ORDER BY re.timestamp DESC
        """)
        print(f"Executing REview Query - {review_query}")
        conn = g.conn
        result = conn.execute(review_query)
        reviews = result.fetchall()
        return render_template("reviews.html", reviews=reviews)
    except Exception as e:
        return f"Error: {e}"

#used to add reviews
@app.route("/add_review", methods=["GET", "POST"])
def add_review():
    print("Executing add review")
    try:
        if request.method == "POST":
            usr_id = request.form["user_id"]
            bok_id = request.form["book_id"]
            cont = request.form["content"]

            g.conn.execute(
                text("INSERT INTO reviews (userid, bookid, com_content) VALUES (:user_id, :book_id, :content)"),
                {"user_id": usr_id, "book_id": bok_id, "content": cont}
            )
            g.conn.commit()
            print("Added book review")
            return redirect("/reviews")

         # fetch users and books from the dropdown
        users = g.conn.execute(text("SELECT userid, username FROM users")).fetchall()
        books = g.conn.execute(text("SELECT bookid, book_title FROM books")).fetchall()
        print("fecthing books and users")
        return render_template("add_review.html", users=users, books=books)

    except Exception as e:
        return f"Error: {e}"


@app.route("/rate_book", methods=["GET", "POST"])
def rate_book():
    print("Executing rate Book")
    if request.method == "POST":
        usr_id = request.form["user_id"]
        bok_id = request.form["book_id"]
        scor = request.form["score"]

        try:
            # CWe first check and see if there is an existing rating
            exists = g.conn.execute(text("""
                SELECT * FROM ratings WHERE userid = :uid AND bookid = :bid
            """), {"uid": usr_id, "bid": bok_id}).fetchone()
            print(f"Rating Exists - {exists}")
            if exists:
                 # If so we update the existing rating
                g.conn.execute(text("""
                    UPDATE ratings SET score = :score
                    WHERE userid = :uid AND bookid = :bid
                """), {"score": scor, "uid": usr_id, "bid": bok_id})
                print("Updating Existing Rating")
            else:
                  # If not we insert a new rating
                print("Creating new Rating")
                g.conn.execute(text("""
                    INSERT INTO ratings (userid, bookid, score) VALUES (:uid, :bid, :score)
                """), {"uid": usr_id, "bid": bok_id, "score": scor})

            g.conn.commit()
            return redirect("/ratings")
        
        except Exception as e:
            return f"Error: {e}"

    users = g.conn.execute(text("SELECT userid, username FROM users")).fetchall()
    books = g.conn.execute(text("SELECT bookid, book_title FROM books")).fetchall()

    return render_template("rate_book.html", users=users, books=books)

#This shows the page of existing ratings. 
@app.route("/ratings")
def ratings():
    print("Executing Ratings")
    try:
        rating_query = text("""
            SELECT rat.userid, u.username, rat.bookid, b.book_title, rat.score
            FROM ratings rat
            JOIN users u ON rat.userid = u.userid
            JOIN books b ON rat.bookid = b.bookid
            ORDER BY rat.userid, rat.bookid
        """)
        #above is our query for ratings 
        print(f"Executing Query - {rating_query}")
        result = g.conn.execute(rating_query)
        ratings = result.fetchall()
        return render_template("ratings.html", ratings=ratings)
    except Exception as e:
        return f"Error: {e}"


# used to add comments to the reviews 
@app.route("/add_comment", methods=["GET", "POST"])
def add_comment():
    print("Executing Add Comment")
    if request.method == "POST":
        usr_id = request.form["user_id"]
        rev_id = request.form["review_id"]
        com_cont = request.form["com_content"]

        try:
            g.conn.execute(
                text("INSERT INTO comments (userid, reviewid, com_content) VALUES (:user_id, :review_id, :com_content)"),
                {"user_id": usr_id, "review_id": rev_id, "com_content": com_cont}
            )
            print("Successfully added review comments")
            g.conn.commit()
            return redirect("/comments")
        except Exception as e:
            return f"Error: {e}"

      # Gets the users and the reviews
    users = g.conn.execute(text("SELECT userid, username FROM users")).fetchall()
    reviews = g.conn.execute(text("""
        SELECT re.reviewid, b.book_title, u.username 
        FROM reviews re
        JOIN books b ON re.bookid = b.bookid
        JOIN users u ON re.userid = u.userid
    """)).fetchall()

    return render_template("add_comment.html", users=users, reviews=reviews)



@app.route("/comments")
def comments():
    print("Executing Comments") # orunts that comments are executing 
    try:
        s_query = text("""
            SELECT com.commentid, u.username, re.com_content, com.com_content, com.timestamp
            FROM comments com
            JOIN users u ON com.userid = u.userid
            JOIN reviews re ON com.reviewid = re.reviewid
            ORDER BY com.timestamp DESC
        """)
        print(s_query)
        result = g.conn.execute(s_query)
        comments = result.fetchall()
        return render_template("comments.html", comments=comments)
    except Exception as e:
        return f"Error: {e}"



@app.route("/add_favorite", methods=["GET", "POST"])
#impliments the addition of the favorites for each user
def add_favorite():
    print("Executing add favourites")
    if request.method == "POST":
        usr_id = request.form["user_id"]
        bok_id = request.form["book_id"]

        try:
            g.conn.execute(
                text("INSERT INTO favorites (userid, bookid) VALUES (:user_id, :book_id)"),
                {"user_id": usr_id, "book_id": bok_id}
            )
            print("Adding Favorites")
            g.conn.commit()
            return redirect("/favorites")
        except Exception as e:
            return f"Error: {e}"

     # Used for the dropdowns. 
    print("Render users and books")
    users = g.conn.execute(text("SELECT userid, username FROM users")).fetchall()
    books = g.conn.execute(text("SELECT bookid, book_title FROM books")).fetchall()

    return render_template("add_favorite.html", users=users, books=books)

@app.route("/favorites")
def favorites():
    print("Executing favorites List")
    try:
        slt_query = text("""
            SELECT fav.userid, u.username, fav.bookid, b.book_title
            FROM favorites fav
            JOIN users u ON fav.userid = u.userid
            JOIN books b ON fav.bookid = b.bookid
            ORDER BY u.username
        """)
        print(f"Executing Qry - {slt_query}")
        result = g.conn.execute(slt_query)
        favorites = result.fetchall()
        return render_template("favorites.html", favorites=favorites)
    except Exception as e:
        return f"Error: {e}"

#impliments the genre 
@app.route("/genres")
def genres():
    print("Executing Generes List")
    try:
        query = text("SELECT genreid, genrename FROM genres ORDER BY genrename")
        print(f"Executing Select Query - {query}")
        result = g.conn.execute(query)
        genres = result.fetchall()
        return render_template("genres.html", genres=genres)
    except Exception as e:
        return f"Error: {e}"


#impliments the authors
@app.route("/authors")
def authors():
    print("Executing Authors List")
    try:
        select_query = text("""
            SELECT a.authorid, a.name, a.year_of_birth, a.nationality
            FROM authors a
            ORDER BY a.name
        """)
        print(f" Executing Authors query - {select_query}")
        result = g.conn.execute(select_query)
        authors = result.fetchall()
        return render_template("authors.html", authors=authors)
    except Exception as e:
        return f"Error: {e}"

#shows the top books
@app.route("/top_books")
def top_books():
    print("Executing Top Books List")
    try:
        query = text("""
            SELECT b.book_title, ROUND(AVG(rat.score), 2) AS average_rating
            FROM books b
            JOIN ratings rat ON b.bookid = rat.bookid
            GROUP BY b.book_title
            ORDER BY average_rating DESC
            LIMIT 10
        """)
        print(f" Fetching Top Books by Rating {query}")
        #we limited amount of books shown to 10 so that you get the top books
        conn = g.conn
        result = conn.execute(query)
        top_books = result.fetchall()
        return render_template("top_books.html", top_books=top_books)
    except Exception as e:
        return f"Error: {e}"


#shows the review by genre 
@app.route("/reviews_by_genre", methods=["GET", "POST"])
def reviews_by_genre():
    print("Executing Reviews by Genre List")
    try:
        if request.method == "POST":
            genre_id = request.form["genre_id"]

            query = text("""
                SELECT b.book_title, u.username, r.com_content, r.timestamp
                FROM reviews r
                JOIN users u ON r.userid = u.userid
                JOIN books b ON r.bookid = b.bookid
                JOIN bookgenres bkg ON b.bookid = bkg.bookid
                JOIN genres ge ON bkg.genreid = ge.genreid
                WHERE ge.genreid = :genre_id
                ORDER BY r.timestamp DESC
            """)
            print(f" Fetching Top REview by GEnre {query}")
            result = g.conn.execute(query, {"genre_id": genre_id})
            reviews = result.fetchall()
             #Gives us the review by genre
            
            genres = g.conn.execute(text("SELECT genreid, genrename FROM genres")).fetchall()

            return render_template("reviews_by_genre.html", reviews=reviews, genres=genres, selected_genre=genre_id)

        
        genres = g.conn.execute(text("SELECT genreid, genrename FROM genres")).fetchall()
        return render_template("reviews_by_genre.html", genres=genres)

    except Exception as e:
        return f"Error: {e}"

#Still shows reviews without comments too, which is why we used a left join
@app.route("/reviews_with_comments")
def reviews_with_comments():
    print("Executing reviews with comments List")
    try:
        query = text("""
            SELECT 
                r.reviewid, 
                b.book_title, 
                r.com_content AS review_content,
                u.username AS reviewer,
                com.commentid,
                com.com_content AS comment_content,
                cu.username AS commenter,
                com.timestamp
            FROM reviews r
            JOIN books b ON r.bookid = b.bookid
            JOIN users u ON r.userid = u.userid
            LEFT JOIN comments com ON com.reviewid = r.reviewid
            LEFT JOIN users cu ON cu.userid = com.userid
            ORDER BY r.reviewid, com.timestamp
        """)
        print(f" GEt all the review with comments {query}")
        result = g.conn.execute(query)
        rows = result.fetchall()
        
        # So that they are clustered by review
        reviews = {}
        print("Create Review Dictionary")
        for row in rows:
            review_id = row[0]
            if review_id not in reviews:
                reviews[review_id] = {
                    "book_title": row[1],
                    "review_content": row[2],
                    "reviewer": row[3],
                    "comments": []
                }
            if row[4]:  # if a comment exists alresy
                reviews[review_id]["comments"].append({
                    "comment_id": row[4],
                    "comment_content": row[5],
                    "commenter": row[6],
                    "timestamp": row[7]
                })
        
        return render_template("reviews_with_comments.html", reviews=reviews)
    
    except Exception as e:
        return f"Error: {e}"




@app.route("/add_genre", methods=["GET", "POST"])
def add_genre():
    print("Executing add Genre List")
    if request.method == "POST":
        genre_name = request.form["genre_name"]

        # Check if the genre already exists
        exists = g.conn.execute(text("""
            SELECT * FROM genres WHERE genrename ILIKE :gname
        """), {"gname": genre_name}).fetchone()
        print(f"Genre Exisits - {exists}")
        if not exists:
            g.conn.execute(text("INSERT INTO genres (genrename) VALUES (:gname)"), {"gname": genre_name})
            g.conn.commit()

        return redirect("/genres")

    return render_template("add_genre.html")

#check for parameters to add the author, cant add book without author 
@app.route("/add_author", methods=["GET", "POST"])
def add_author():
    print("Executing add author List")
    if request.method == "POST":
        name = request.form["name"]
        year_of_birth = request.form["year_of_birth"]
        nationality = request.form["nationality"]

        # Sees if the author already exists
        exists = g.conn.execute(text("""
            SELECT * FROM authors WHERE name ILIKE :name
        """), {"name": name}).fetchone()
        print(f"Author Exists {exists}")
        if not exists:
            g.conn.execute(text("""
                INSERT INTO authors (name, year_of_birth, nationality)
                VALUES (:name, :year_of_birth, :nationality)
            """), {"name": name, "year_of_birth": year_of_birth, "nationality": nationality})
            g.conn.commit()
            print("Author added successfully")

        return redirect("/authors")

    return render_template("add_author.html")

#Method to delete a book, no moderator
@app.route("/delete_book/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    print("Executing delete book")
    g.conn.execute(text("DELETE FROM books WHERE bookid = :bid"), {"bid": book_id})
    g.conn.commit()
    return redirect("/books")




#method for seacrh used left join
@app.route("/search")
def search():
    print("Executing search List")
    query = request.args.get('query', '')
    try:
        search_sql = text("""
            SELECT b.book_title, b.combined_rating, a.name AS author_name
            FROM books b
            LEFT JOIN book_authors bka ON b.bookid = bka.bookid
            LEFT JOIN authors a ON bka.authorid = a.authorid
            WHERE b.book_title ILIKE :q OR a.name ILIKE :q
        """)
        print(f"Executing Query {search_sql}")
        result = g.conn.execute(search_sql, {"q": f"%{query}%"}).fetchall()
        return render_template("search_results.html", query=query, results=result)
    except Exception as e:
        return f"Error searching: {e}"


@app.route("/author_books/<int:author_id>")
def author_books(author_id):
    print("Executing Author Books List")
    select_query = text("""
        SELECT b.bookid, b.book_title, b.isbn, b.combined_rating
        FROM books b
        JOIN book_authors ba ON b.bookid = ba.bookid
        WHERE ba.authorid = :aid
    """)
    print(select_query)
    conn = g.conn
    books = conn.execute(select_query, {"aid": author_id}).fetchall()
    return render_template("author_books.html", books=books)

#no moderator so anyone can change it 
@app.route("/delete_author/<int:author_id>", methods=["POST"])
def delete_author(author_id):
    print("Executing Delete Author")
    g.conn.execute(text("DELETE FROM authors WHERE authorid = :aid"), {"aid": author_id})
    g.conn.commit()
    print(f"Deleted author {author_id} Successfully ")
    return redirect("/authors")

#no moderator so anyone can change it 
@app.route("/delete_genre/<int:genre_id>", methods=["POST"])
def delete_genre(genre_id):
    print("Executing Delete Genre")
    g.conn.execute(text("DELETE FROM genres WHERE genreid = :gid"), {"gid": genre_id})
    g.conn.commit()
    print(f"Deleted Genere {genre_id} Successfully ")
    return redirect("/genres")


@app.route("/delete_review/<int:review_id>", methods=["POST"])
def delete_review(review_id):
    print("Executing Delete Review")
    user_id = request.form["user_id"]
    # we collect the user id , so that only the user can delete
    check = g.conn.execute(text("""
        SELECT * FROM reviews WHERE reviewid = :rid AND userid = :uid
    """), {"rid": review_id, "uid": user_id}).fetchone()
    print(f"review exists - {check}")
    if check:
        g.conn.execute(text("DELETE FROM reviews WHERE reviewid = :rid"), {"rid": review_id})
        g.conn.commit()
        print("Deleted review successfully")

    return redirect("/reviews")



@app.route("/delete_comment/<int:comment_id>", methods=["POST"])
def delete_comment(comment_id):
    print("Executing Delete Comment")
    user_id = request.form["user_id"]
    # we collect the user id , so that only the user can delete
    check = g.conn.execute(text("""
        SELECT * FROM comments WHERE commentid = :cid AND userid = :uid
    """), {"cid": comment_id, "uid": user_id}).fetchone()
    print(f"comment exists - {check}")
    if check:
        print("Deleted comment successfully")
        g.conn.execute(text("DELETE FROM comments WHERE commentid = :cid"), {"cid": comment_id})
        g.conn.commit()

    return redirect("/comments")


@app.route("/delete_rating/<int:book_id>", methods=["POST"])
def delete_rating(book_id):
    print("Executing Delete Rating")
    user_id = request.form["user_id"]
    # we collect the user id , so that only the user can delete
    check = g.conn.execute(text("""
        SELECT * FROM ratings WHERE bookid = :bid AND userid = :uid
    """), {"bid": book_id, "uid": user_id}).fetchone()
    print(f"rating exists - {check}")
    if check:
        g.conn.execute(text("""
            DELETE FROM ratings WHERE bookid = :bid AND userid = :uid
        """), {"bid": book_id, "uid": user_id})
        print("Deleted rating successfully")
        g.conn.commit()

    return redirect("/ratings")


@app.route("/delete_favorite/<int:book_id>", methods=["POST"])
def delete_favorite(book_id):
    print("Executing Delete Favorite")
    user_id = request.form["user_id"]
    # we collect the user id , so that only the user can delete
    check = g.conn.execute(text("""
        SELECT * FROM favorites WHERE bookid = :bid AND userid = :uid
    """), {"bid": book_id, "uid": user_id}).fetchone()
    print(f"favorite exists - {check}")
    if check:
        g.conn.execute(text("""
            DELETE FROM favorites WHERE bookid = :bid AND userid = :uid
        """), {"bid": book_id, "uid": user_id})
        g.conn.commit()
        print("Deleted favorite successfully")

    return redirect("/favorites")



run()
