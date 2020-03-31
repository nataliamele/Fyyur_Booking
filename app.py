#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import json
import dateutil.parser
from datetime import datetime
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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
  return babel.dates.format_datetime(date, format)

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

  data =[]
  locations = Venue.query.with_entities(func.count(Venue.id), Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()

  for venue_loc in locations:
    venue_by_loc = Venue.query.filter_by(state = venue_loc.state).filter_by(city = venue_loc.city).all()
    venue_info = []
    for venue in venue_by_loc:
      venue_info.append(
        {
          "id": venue.id,
          "name": venue.name, 
          "num_upcoming_shows":
          len(Show.query.filter(Show.venue_id == venue.id).filter(Show.start_time>datetime.now()).all())
        }
      )
    data.append({
      "city": venue_loc.city,
      "state": venue_loc.state ,
      "venues": venue_info
    })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  search_res = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  
  data =[]

  for res in search_res:
    data.append(
      {
          "id": res.id,
          "name": res.name, 
          "num_upcoming_shows":
          len(Show.query.filter(Show.venue_id == Venue.id).filter(Show.start_time>datetime.now()).all())
        }
    )
  response={
    "count": len(search_res),
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  
  venue = Venue.query.get(venue_id)
  
  upcoming = Show.query.join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time>datetime.now()).all()
  past = Show.query.join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time<datetime.now()).all()

  shows_upcoming = []
  for show in upcoming:
    shows_upcoming.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })
  shows_past=[]
  for show in past:
    shows_past.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })
  data = {
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
    "past_shows": shows_past,
    "upcoming_shows": shows_upcoming,
    "past_shows_count": len(shows_past),
    "upcoming_shows_count": len(shows_upcoming)   
  }
  
  return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  
  try:
    v_name = request.form['name']
    v_city = request.form['city']
    v_state = request.form['state']
    v_address = request.form['address']
    v_phone = request.form['phone']
    v_image_link = request.form['image_link']
    v_genres = request.form.getlist('genres')
    v_facebook_link = request.form['facebook_link']
    v_website = request.form['website']
    v_seeking_talent = True if 'seeking_talent' in request.form else False
    v_seeking_description = request.form['seeking_description']

    venue = Venue(name = v_name, city= v_city, state = v_state, address= v_address, phone = v_phone, image_link = v_image_link, genres =v_genres, facebook_link = v_facebook_link, website= v_website, seeking_talent= v_seeking_talent, seeking_description= v_seeking_description)
    
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name']  + ' could not be listed.')
    print(sys.exc_info())

  finally:
    db.session.close()
  
  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

  try: 
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash(f'Venue {venue_id} was successfully deleted.')
    return render_template('pages/home.html')
  except: 
    db.session.rollback()
    flash(f'Venue {venue_id} was not deleted :(')
    print(sys.exc_info())
  finally: 
    db.session.close()
 
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  data = []
  artists_all = Artist.query.all()

  for artist in artists_all:
    data.append({
      "id": artist.id,
      "name":artist.name
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  search_res = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

  data = []

  for res in search_res:
    data.append({
      "id": res.id,
      "name": res.name,
      "num_upcoming_shows": len(Show.query.filter(Show.artist_id == Artist.id).filter(Show.start_time >datetime.now()).all())
    })

  response = {
    "count": len(search_res),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  artist = Artist.query.get(artist_id)

  if not artist: return render_template('errors/404.html')

  upcoming = Show.query.join(Artist).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time > datetime.now()).all()
  past = Show.query.join(Artist).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time < datetime.now()).all()

  shows_upcoming = []

  for show in upcoming: 
    shows_upcoming.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })

  shows_past = []
  for show in past: 
    shows_past.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": shows_past,
    "upcoming_shows": shows_upcoming,
    "past_shows_count": len(shows_past),
    "upcoming_shows_count": len(shows_upcoming),
  }  
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  artist = Artist.query.get(artist_id)

  if artist: 
    form.name.data = artist.name
    form.genres.data = artist.genres
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data =  artist.phone
    form.website.data = artist.website
    form.facebook_link.data =  artist.facebook_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data =  artist.seeking_description
    form.image_link.data =  artist.image_link  

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  error = False 
  artist = Artist.query.get(artist_id)

  try: 
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.image_link = request.form['image_link']
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form['facebook_link']
    artist.website = request.form['website']
    artist.seeking_venue = True if 'seeking_venue' in request.form else False
    artist.seeking_description = request.form['seeking_description']

    db.session.commit()
    flash('Artist information was updated successfully!')
  except:
    error = True
    db.session.rollback()
    flash('An error occured. Artist information could not be edited.')
    print(sys.exc_info())
  finally:
    db.session.close()
  
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  if venue: 
    form.name.data = venue.name
    form.genres.data = venue.genres
    form.address.data = venue.address
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data =  venue.phone
    form.image_link.data =  venue.image_link 
    form.website.data = venue.website
    form.facebook_link.data =  venue.facebook_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data =  venue.seeking_description
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  
  error = False
  venue = Venue.query.get(venue_id)
  try: 
    venue.name = request.form['name']
    venue.genres = request.form.getlist('genres')
    venue.address = request.form['address']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.phone = request.form['phone']
    venue.image_link = request.form['image_link']
    venue.website = request.form['website']
    venue.facebook_link = request.form['facebook_link']
    venue.seeking_talent=  True if 'seeking_talent' in request.form else False
    venue.seeking_description = request.form['seeking_description']

    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if not error: 
    flash('Venue information was updated successfully!')
  else:
    flash('An error occured. Venue information could not be edited.')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])

def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  
  error = False 

  try:
    name =  request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    image_link = request.form['image_link']
    genres = request.form.getlist('genres')
    website = request.form['website']
    fb_link = request.form['facebook_link']
    seeking_venue = True if 'seeking_venue' in request.form else False
    seeking_desc = request.form['seeking_description']


    new_artist = Artist(name = name, genres = genres, city = city, state = state, phone = phone, website = website, facebook_link = fb_link, seeking_venue = seeking_venue, seeking_description = seeking_desc, image_link = image_link)

    db.session.add(new_artist)
    db.session.commit()
  
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  finally: 
    db.session.close()
    
  if not error:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  else:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  all_shows = Show.query.join(Artist).join(Venue).all()

  data = []

  for show in all_shows:
    data.append({
      'venue_id': show.venue_id,
      'venue_name': show.venue.name,
      'artist_id': show.artist_id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
    
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  error = False

  try: 
    new_artist = request.form['artist_id']
    new_venue = request.form['venue_id']
    new_time = request.form['start_time']

    new_show = Show(artist_id = new_artist, venue_id = new_venue, start_time = new_time)

    db.session.add(new_show)
    db.session.commit()
  except: 
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  
  if not error: flash('Show was successfully listed!')
  else: flash('Could not add new show.')

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

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
