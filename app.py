#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#


import jsonify
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from forms import *
import sys
from sqlalchemy.orm import load_only
from sqlalchemy import distinct
import datetime

from models import Venue, Venue_Genre, Artist, Artist_Genre, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    
    response_data = []

    try:
        venue_locations = db.session.query(distinct(Venue.city), Venue.state).all()

        today = datetime.datetime.now()

        for location in venue_locations:
            city = location[0]
            state = location[1]

            location_data = {"city": city, "state": state, "venues": []}

            venues = Venue.query.filter_by(city=city, state=state).all()

            for venue in venues:
                venue_name = venue.name
                venue_id = venue.id

                upcoming_shows = (
                    Show.query.filter_by(venue_id=venue_id)
                    .filter(Show.start_time > today)
                    .all()
                )

                venue_data = {
                    "id": venue_id,
                    "name": venue_name,
                    "num_upcoming_shows": len(upcoming_shows),
                }

                location_data["venues"].append(venue_data)

            response_data.append(location_data)

    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("Something went wrong. Please try again.")
        return render_template("pages/home.html")

    finally:
         return render_template('pages/venues.html', areas=response_data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_query = request.form.get("search_term", "")

    search_response = {"count": 0, "data": []}

    fields = ["id", "name"]
    venue_search_results = (
        db.session.query(Venue)
        .filter(Venue.name.ilike(f"%{search_query}%"))
        .options(load_only(*fields))
        .all()
    )

    search_response["count"] = len(venue_search_results)

    for result in venue_search_results:
        item = {
            "id": result.id,
            "name": result.name,
        }
        search_response["data"].append(item)

    return render_template(
        "pages/search_venues.html",
        results=search_response,
        search_term=request.form.get("search_term", ""),
    )



# shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    data = {}

    try:
        requested_venue = Venue.query.get(venue_id)

        if requested_venue is None:
            return not_found_error(404)

        genres = []
        for item in requested_venue.genres:
            genres.append(item.genre)

        shows = Show.query.filter_by(venue_id=venue_id)

        today = datetime.datetime.now()

        raw_past_shows = shows.filter(Show.start_time < today).all()
        past_shows = []
        for show in raw_past_shows:
            artist = Artist.query.get(show.artist_id)
            show_data = {
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": str(show.start_time),
            }
            past_shows.append(show_data)

        raw_upcoming_shows = shows.filter(Show.start_time >= today).all()
        upcoming_shows = []
        for show in raw_upcoming_shows:
            artist = Artist.query.get(show.artist_id)
            show_data = {
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": str(show.start_time),
            }
            upcoming_shows.append(show_data)

        data = {
            "id": requested_venue.id,
            "name": requested_venue.name,
            "genres": genres,
            "address": requested_venue.address,
            "city": requested_venue.city,
            "state": requested_venue.state,
            "phone": requested_venue.phone,
            "website": requested_venue.website,
            "facebook_link": requested_venue.facebook_link,
            "seeking_talent": requested_venue.seeking_talent,
            "image_link": requested_venue.image_link,
            "past_shows": past_shows,
            "upcoming_shows": upcoming_shows,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows),
        }

    except:
        print(sys.exc_info())
        flash("Something went wrong. Please try again.")

    finally:
        db.session.close()

    return render_template("pages/show_venue.html", venue=data)



#  Create Venue
#  ----------------------------------------------------------------



@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)




 # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  
  
@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    
    checked=''
    form = VenueForm()
    if(request.form.get('seeking_talent')=="yes"):
        checked = True
    else:
        checked = False
    try:
        name = request.form.get("name")
        city = request.form.get("city")
        state = request.form.get("state")
        address = request.form.get("address")
        phone = request.form.get("phone")
        genres = request.form.getlist("genres")
        facebook_link = request.form.get("facebook_link")
        website = request.form.get("website")
        seeking_talent = checked,
        seeking_description = request.form.get("seeking_description")
        image_link = request.form.get("image_link")

        new_venue = Venue(
            name=name,
            city=city,
            state=state,
            address=address,
            phone=phone,
            facebook_link=facebook_link,
            website = website,
            seeking_talent = seeking_talent,
            seeking_description = seeking_description,
            image_link = image_link
        )

        genres_for_this_venue = []
        for genre in genres:
            current_genre = Venue_Genre(genre=genre)
            current_genre.venue = new_venue
            genres_for_this_venue.append(current_genre)

        db.session.add(new_venue)
        db.session.commit()

        db.session.refresh(new_venue)
        flash("Venue " + new_venue.name + " was successfully listed!")

    except:
        db.session.rollback()
        print(sys.exc_info())
        flash(
            "An error occurred. Venue "
            + request.form.get("name")
            + " could not be listed."
        )

    finally:
        db.session.close()
        return render_template("pages/home.html")



# TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
@app.route('/venues/<venue_id>/delete', methods=['DELETE'])
def delete_venue(venue_id):
    venue_name = Venue.query.get(venue_id).name
    try:
        venue_to_be_deleted = db.session.query(Venue).filter(Venue.id == venue_id)
        venue_to_be_deleted.delete()
        db.session.commit()
        flash("Venue: " + venue_name + " was successfully deleted.")

    except:
        db.session.rollback()
        print(sys.exc_info())
        return jsonify(
            {
                "errorMessage": "Something went wrong. This venue was not successfully deleted. Please try again."
            }
        )

    finally:
        db.session.close()
        return redirect(url_for("index"))




#  Artists
#  ----------------------------------------------------------------

@app.route('/artists')
def artists():
    fields = ["id", "name"]
    artists_data = db.session.query(Artist).options(load_only(*fields)).all()

    return render_template("pages/artists.html", artists=artists_data)



# TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  
  
@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_query = request.form.get("search_term", "")

    search_response = {"count": 0, "data": []}

    fields = ["id", "name"]
    artist_search_results = (
        db.session.query(Artist)
        .filter(Artist.name.ilike(f"%{search_query}%"))
        .options(load_only(*fields))
        .all()
    )

    num_upcoming_shows = 0

    search_response["count"] = len(artist_search_results)

    for result in artist_search_results:
        item = {
            "id": result.id,
            "name": result.name,
            "num_upcoming_shows": num_upcoming_shows,
        }
        search_response["data"].append(item)

    return render_template(
        "pages/search_artists.html",
        results=search_response,
        search_term=request.form.get("search_term", ""),
    )



 # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  
  
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    data = {}

    try:
        requested_artist = Artist.query.get(artist_id)

        if requested_artist is None:
            return not_found_error(404)
            # Figure out a better way to do this

        genres = []
        for item in requested_artist.genres:
            genres.append(item.genre)


        today = datetime.datetime.now()

        past_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>today).all()
        past_shows = []
        for query in past_shows_query:
            
            show_data = {
                "venue_id": query.id,
                "venue_name": query.name,
                "venue_image_link": query.image_link,
                "start_time": str(query.start_time),
            }
            past_shows.append(show_data)

        upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>today).all()
        upcoming_shows = []
        for query in upcoming_shows_query:
            
            show_data = {
                "venue_id": query.id,
                "venue_name": query.name,
                "venue_image_link": query.image_link,
                "start_time": str(query.start_time),
            }
            upcoming_shows.append(show_data)

        data = {
            "id": requested_artist.id,
            "name": requested_artist.name,
            "genres": genres,
            "city": requested_artist.city,
            "state": requested_artist.state,
            "phone": requested_artist.phone,
            "seeking_venue": requested_artist.seeking_venue,
            "facebook_link": requested_artist.facebook_link,
            "image_link": requested_artist.image_link,
            "website_link" : requested_artist.website_link,
            "past_shows": past_shows,
            "upcoming_shows": upcoming_shows,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows),
        }

    except:
        print(sys.exc_info())
        flash("Something went wrong. Please try again.")

    finally:
        db.session.close()

    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    
    form = ArtistForm()
    checked=''
    
    if(request.form.get('seeking_venue')=="yes"):
        checked = True
    else:
        checked = False

    data = {}

    try:
        requested_artist = Artist.query.get(artist_id)
        print(requested_artist)
        if requested_artist is None:
            return not_found_error(404)
            # Figure out a better way to do this

        genres = []
        if len(requested_artist.genres) > 0:
            for item in requested_artist.genres:
                genres.append(item.genre)

        data = {
            "id": requested_artist.id,
            "name": requested_artist.name,
            "city": requested_artist.city,
            "state": requested_artist.state,
            "phone": requested_artist.phone,
            "genres": genres,
            "facebook_link": requested_artist.facebook_link,
            "seeking_venue": checked,
            "seeking_description": requested_artist.seeking_description,
            "image_link": requested_artist.image_link,
            "website_link" : requested_artist.website_link
        }

    except:
        print(sys.exc_info())
        flash("Something went wrong. Please try again.")
        return redirect(url_for("index"))

    finally:
        db.session.close()

    return render_template("forms/edit_artist.html", form=form, artist=data)
  # TODO: populate form with fields from artist with ID <artist_id>
  
  
  
# TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  
  
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    
    checked=''
    form = ArtistForm()
    if(request.form.get('seeking_venue')=="yes"):
        checked = True
    else:
        checked = False
    try:
        artist_to_be_updated = Artist.query.get(artist_id)

        if artist_to_be_updated is None:
            return not_found_error(404)

        name = request.form.get("name")
        city = request.form.get("city")
        state = request.form.get("state")
        phone = request.form.get("phone")
        genres = request.form.getlist("genres")
        facebook_link = request.form.get("facebook_link")
        seeking_venue = checked
        seeking_description = request.form.get("seeking_description")
        website_link = request.form.get("website_link")
        
        
        artist_to_be_updated.name = name
        artist_to_be_updated.city = city
        artist_to_be_updated.state = state
        artist_to_be_updated.phone = phone
        artist_to_be_updated.facebook_link = facebook_link
        artist_to_be_updated.image_link = "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
        artist_to_be_updated.seeking_venue = seeking_venue
        artist_to_be_updated.seeking_description = seeking_description
        artist_to_be_updated.website_link = website_link
        
        genres_for_this_artist = []
        for genre in genres:
            current_genre = Artist_Genre(genre=genre)
            current_genre.artist = artist_to_be_updated
            genres_for_this_artist.append(current_genre)

        db.session.add(artist_to_be_updated)
        db.session.commit()

        db.session.refresh(artist_to_be_updated)
        flash("This venue was successfully updated!")

    except:
        db.session.rollback()
        print(sys.exc_info())
        flash(
            "An error occurred. Venue "
            + request.form.get("name")
            + " could not be updated."
        )

    finally:
        db.session.close()

    return redirect(url_for("show_artist", artist_id=artist_id))



@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    
    data = {}

    try:
        requested_venue = Venue.query.get(venue_id)

        if requested_venue is None:
            return not_found_error(404)
            # Figure out a better way to do this

        genres = []
        if len(requested_venue.genres) > 0:
            for item in requested_venue.genres:
                genres.append(item.genre)

        data = {
            "id": requested_venue.id,
            "name": requested_venue.name,
            "city": requested_venue.city,
            "state": requested_venue.state,
            "address": requested_venue.address,
            "phone": requested_venue.phone,
            "genres": genres,
            "facebook_link": requested_venue.facebook_link,
            "seeking_talent": requested_venue.seeking_talent,
            "seeking_description": requested_venue.seeking_description,
            "image_link": requested_venue.image_link,
            "website": requested_venue.website
        }

    except:
        print(sys.exc_info())
        flash("Something went wrong. Please try again.")
        return redirect(url_for("index"))

    finally:
        db.session.close()

    return render_template("forms/edit_venue.html", form=form, venue=data)

  # TODO: populate form with values from venue with ID <venue_id>
  
  
  
 # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    
    checked=''
    form = VenueForm()
    if(request.form.get('seeking_talent')=="yes"):
        checked = True
    else:
        checked = False
    try:
        name = request.form.get("name")
        city = request.form.get("city")
        state = request.form.get("state")
        address = request.form.get("address")
        phone = request.form.get("phone")
        genres = request.form.getlist("genres")
        facebook_link = request.form.get("facebook_link")
        seeking_talent = checked
        seeking_description = request.form.get("seeking_description")
        website = request.form.get("website")
        

        venue_to_be_updated = Venue.query.get(venue_id)

        venue_to_be_updated.name = name
        venue_to_be_updated.city = city
        venue_to_be_updated.state = state
        venue_to_be_updated.address = address
        venue_to_be_updated.phone = phone
        venue_to_be_updated.facebook_link = facebook_link
        venue_to_be_updated.seeking_talent = seeking_talent
        venue_to_be_updated.seeking_description = seeking_description
        venue_to_be_updated.website = website

        genres_for_this_venue = []
        for genre in genres:
            current_genre = Venue_Genre(genre=genre)
            current_genre.venue = venue_to_be_updated
            genres_for_this_venue.append(current_genre)

        db.session.add(venue_to_be_updated)
        db.session.commit()

        db.session.refresh(venue_to_be_updated)
        flash("This venue was successfully updated!")

    except:
        db.session.rollback()
        print(sys.exc_info())
        flash(
            "An error occurred. Venue "
            + request.form.get("name")
            + " could not be updated."
        )

    finally:
        db.session.close()

    return redirect(url_for("show_venue", venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)



# called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  
  
@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    
    checked=''
    form = ArtistForm()
    if(request.form.get('seeking_venue')=="yes"):
        checked = True
    else:
        checked = False 
        
    try:
        name = request.form.get("name")
        city = request.form.get("city")
        state = request.form.get("state")
        phone = request.form.get("phone")
        genres = request.form.getlist("genres")
        facebook_link = request.form.get("facebook_link")
        seeking_venue = checked
        seeking_description = request.form.get("seeking_description")
        website_link = request.form.get("website_link")
        

        new_artist = Artist(
            name=name, city=city, state=state, phone=phone, facebook_link=facebook_link,
            seeking_venue = seeking_venue, seeking_description=seeking_description, website_link=website_link
        )

        genres_for_this_artist = []
        for genre in genres:
            current_genre = Artist_Genre(genre=genre)
            current_genre.artist = new_artist
            genres_for_this_artist.append(current_genre)

        db.session.add(new_artist)
        db.session.commit()

        db.session.refresh(new_artist)
        flash("Artist " + new_artist.name + " was successfully listed!")

    except:
        db.session.rollback()
        print(sys.exc_info())
        flash(
            "An error occurred. Venue "
            + request.form.get("name")
            + " could not be listed."
        )

    finally:
        db.session.close()
        return render_template("pages/home.html")



#  Shows
#  ----------------------------------------------------------------
 # displays list of shows at /shows
  # TODO: replace with real venues data.
  
@app.route('/shows')
def shows():
   
    all_shows_data = []

    try:
        shows = Show.query.all()
        for show in shows:
            venue_id = show.venue_id
            artist_id = show.artist_id
            artist = Artist.query.get(artist_id)

            each_show_data = {
                "venue_id": venue_id,
                "venue_name": Venue.query.get(venue_id).name,
                "artist_id": artist_id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": str(show.start_time),
            }

            all_shows_data.append(each_show_data)

    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("Something went wrong, please try again.")

    finally:
        return render_template("pages/shows.html", shows=all_shows_data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)



# called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  
  
@app.route('/shows/create', methods=['POST'])
def create_show_submission():

    errors = {"invalid_artist_id": False, "invalid_venue_id": False}

    try:
        artist_id = request.form.get("artist_id")
        venue_id = request.form.get("venue_id")
        start_time = request.form.get("start_time")

        found_artist = Artist.query.get(artist_id)
        if found_artist is None:
            errors["invalid_artist_id"] = True

        found_venue = Venue.query.get(venue_id)
        if found_venue is None:
            errors["invalid_venue_id"] = True

        if found_venue is not None and found_artist is not None:
            new_show = Show(
                artist_id=found_artist.id,
                venue_id=found_venue.id,
                start_time=start_time,
            )
            db.session.add(new_show)
            db.session.commit()
            flash(
                "The show by "
                + found_artist.name
                + " has been successfully scheduled at the following venue: "
                + found_venue.name
            )

    except:
        print(sys.exc_info())
        db.session.rollback()
        flash("Something went wrong and the show was not created. Please try again.")

    finally:
        db.session.close()

    if errors["invalid_artist_id"] is True:
        flash(
            "There is no artist with id "
            + request.form.get("artist_id")
            + " in our records"
        )
    elif errors["invalid_venue_id"] is True:
        flash(
            "There is no venue with id "
            + request.form.get("venue_id")
            + " in our records"
        )

    return render_template("pages/home.html")

    flash("Show was successfully listed!")

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#


db.create_all()

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
