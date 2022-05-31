#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import os
import sys
import dateutil.parser
import babel
from sqlalchemy import func
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler 
from forms import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

SQLALCHEMY_DATABASE_URI = 'postgresql://japhheth@localhost:5432/fyyur'

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

from models import *

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format,locale='en')

app.jinja_env.filters['datetime'] = format_datetime


# Controllers.


@app.route('/')
def index():
  return render_template('pages/home.html')



# Fetch all venues 

@app.route('/venues')
def venues():
   # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  all_venues = Venue.query.with_entities(func.count(Venue.id), Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()

  data = []


  for venue in all_venues:
      areas = Venue.query.filter_by(state=venue.state).filter_by(city=venue.city).all()
      sub_venue_arr = []
      for area in areas: 
        sub_venue_arr.append({
            'id': area.id,
            'name': area.name,
            'num_upcoming_shows': len(list(Show.query.filter(Show.venue_id==1).filter(Show.start_time>datetime.now()).all()))
        })
        data.append({
            "city": area.city,
            "state": area.state, 
            "venues": sub_venue_arr
        })

  return render_template('pages/venues.html', areas=data);


# Venue Search 
@app.route('/venues/search', methods=['POST'])
def search_venues():
   # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # search for Hop should return "The Musical Hop".
  # search for "Music" should return "Ghana Festival" and "London"
   serach_value = request.form.get('search_term')
   filtered_venues = Venue.query.filter(
        Venue.name.ilike('%{}%'.format(serach_value))).all()

   data = []
   for venue in filtered_venues:
        obj = {}
        obj['id'] = venue.id
        obj['name'] = venue.name
        obj['num_upcoming_shows'] = len(venue.shows)
        data.append(obj)
        response = {}
        response['count'] = len(data)
        response['data'] = data

        return render_template('pages/search_venues.html', results=response, search_term=serach_value)


#Fetch venue by ID

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
   # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)

  if not venue: 
    return render_template('errors/404.html')

  filtered_upcoming_shows = Show.query.join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
  coming_shows = []

  filtered_past_shows = Show.query.join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
  previous_shows = []

  for show in filtered_past_shows:
    previous_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  for show in filtered_upcoming_shows:
    coming_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")    
    })

  response = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": previous_shows,
    "upcoming_shows": coming_shows,
    "past_shows_count": len(previous_shows),
    "upcoming_shows_count": len(coming_shows),
  }

  return render_template('pages/show_venue.html', venue=response)

#  Create Venue
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  
  try: 
    venue = Venue()
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    tmp_genres = request.form.getlist('genres')
    venue.genres = ','.join(tmp_genres)  # convert list to string
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website_link']
    venue.seeking_talent = True if 'seeking_talent' in request.form else False 
    venue.seeking_description = request.form['seeking_description']
    db.session.add(venue)
    db.session.commit()
  except: 
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    flash('An error occurred. Venue ' + request.form['name']+ ' could not be listed.')
  if not error: 
     # on successful db insert, flash success 
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  if venue: 
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.address.data = venue.address
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website_link.data = venue.website
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False  
  venue = Venue.query.get(venue_id)

  try: 
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website_link']
    venue.seeking_talent = True if 'seeking_talent' in request.form else False 
    venue.seeking_description = request.form['seeking_description']

    db.session.commit()
  except: 
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
    flash(f'An error occurred. Venue could not be changed.')
  if not error: 
    flash(f'Venue was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

# Delete Venue
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):  
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error: 
    flash('An error occurred. Venue could not be deleted.')
  if not error: 
    flash('Venue was deleted successfully.')
  return render_template('pages/home.html')



#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()

  return render_template('pages/artists.html', artists=data)

#  Search Artists 
@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_val = request.form.get('search_term', '')
  filtered_val = Artist.query.filter(Artist.name.ilike('%{}%'.format(search_val))).all()
  data = []

  for artist in filtered_val:
    obj = {}
    obj['id'] = artist.id
    obj['name'] = artist.name
    obj['num_upcoming_shows'] = len(Show.query.filter(Show.artist_id == artist.id).filter(Show.start_time > datetime.now()).all())
    data.append(obj)
    payload = {}
    payload['count'] = len(data)
    payload['data'] = data

  return render_template('pages/search_artists.html', results=payload, search_term=search_val)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist_query = Artist.query.get(artist_id)

  if not artist_query: 
    return render_template('errors/404.html')

  filtered_past_shows = Show.query.join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  prev_shows = []

  for show in filtered_past_shows:
    prev_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  filtered_upcoming_shows = Show.query.join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  coming_shows = []

  for show in filtered_upcoming_shows:
    coming_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })


  data = {
    "id": artist_query.id,
    "name": artist_query.name,
    "genres": artist_query.genres,
    "city": artist_query.city,
    "state": artist_query.state,
    "phone": artist_query.phone,
    "website": artist_query.website,
    "facebook_link": artist_query.facebook_link,
    "seeking_venue": artist_query.seeking_venue,
    "seeking_description": artist_query.seeking_description,
    "image_link": artist_query.image_link,
    "past_shows": prev_shows,
    "upcoming_shows": coming_shows,
    "past_shows_count": len(prev_shows),
    "upcoming_shows_count": len(coming_shows),
  }

  return render_template('pages/show_artist.html', artist=data)

# Get artist by ID

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  if artist: 
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.website_link.data = artist.website
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)

# Update artist by ID

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False  
  artist = Artist.query.get(artist_id)

  try: 
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website = request.form['website_link']
    artist.seeking_venue = True if 'seeking_venue' in request.form else False 
    artist.seeking_description = request.form['seeking_description']

    db.session.commit()
  except: 
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
    flash('An error occurred. Artist could not be changed.')
  if not error: 
    flash('Artist was successfully updated!')
  return redirect(url_for('show_artist', artist_id=artist_id))




# Create Artist

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try: 
    artist = Artist() 
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    tmp_genres = request.form.getlist('genres')
    artist.genres = ','.join(tmp_genres)  # convert list to string
    artist.facebook_link = request.form['facebook_link']
    artist.image_link = request.form['image_link']
    artist.website = request.form['website_link']
    artist.seeking_venue = True if 'seeking_venue' in request.form else False
    artist.seeking_description = request.form['seeking_description']
    db.session.add(artist)
    db.session.commit()
  except: 
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
    flash('An error occurred. Artist ' + request.form['name']+ ' could not be listed.')
  if not error: 
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')


#  Get Shows

@app.route('/shows')
def shows():

  shows_query = Show.query.join(Artist).join(Venue).all()

  data = []
  for show in shows_query: 
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name, 
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  return render_template('pages/shows.html', shows=data)


# Create Shows

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try: 
    show = Show()
    show.artist_id = request.form['artist_id']
    show.venue_id = request.form['venue_id']
    show.start_time = request.form['start_time']

    db.session.add(show)
    db.session.commit()
  except: 
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
    flash('An error occurred. Show could not be listed.')
  if not error: 
    flash('Show was successfully listed')
  return render_template('pages/home.html')
    

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

# Launch.

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)