'''
Looking at the movie/series listing uploaded by someone, it's very tempting to 
download them all. Lot of time is spent is checking IMDb pages of those titles.

To reduce the pain, this script fetches file listing from HTTP server.
For each movie title, it's IMDB details are fetched using OMDb API.
Depending upon the IMDb rating, you can choose what to download.

Author: Aboli Aradhye (aboli.a.aradhye@gmail.com)
'''

import re
import csv
import json
import requests
from bs4 import BeautifulSoup

class MovieIndex(object):
	def __init__(self, indexes, genre=None):
		self.movies = {}
		self.indexes = indexes
		self.genre = genre
		self.curIndex = ""
	
	def is_valid_title(self, title):
		# Title should contain atleast one alphabet or number.
		pattern = re.compile(".*[a-zA-Z0-9].*")
		return pattern.match(title)

	def save_imdb_record(self, title):
		if title in self.movies:
			return

		if not self.is_valid_title(title):
			print "Not a valid movie title: %s" %title
			return

		url = "http://www.omdbapi.com/?t=%s&r=json" %title
		response = requests.get(url)
		if response.status_code != 200:
			print "Response from omdbapi: %s" %response.status_code
			return []

		moviedict = json.loads(response.content)
		if moviedict["Response"] == "False":
			print "No movie found: %s" %title
			return

		keys = ["Year", "Genre", "imdbRating"]
		d = {k:v for k,v in moviedict.iteritems() if k in keys}
		d["Year"] = d["Year"][:4]
		d["Index"] = self.curIndex
		self.movies[moviedict["Title"]] = d
		print "Movie details saved for %s" %title

	def format_title(self, title):
		title = title.rstrip("/")

		# Remove year from title
		yearregex = " \((19|20)\d{2}\)$"
		title = re.sub(yearregex, "", title)
		return title

	def get_titles_from_index(self):
		response = requests.get(self.curIndex)
		if response.status_code != 200:
			return []
		fdata = response.content
		fdata = fdata.split('\r')
		soup = BeautifulSoup(''.join(fdata))
		hrefs = soup.findAll('a')
		titles = [self.format_title(h.text) for h in hrefs if h and h.text]
		return titles

	def filter_by_genre(self):
		'''
		If no genres are specified, movies with all genres will be taken.
		Alternatively, if genres are specified, movies with only those genres
		will be considered.
		'''

		genre = self.genre
		if not genre:
			return
		if isinstance(genre, basestring):
			genre = [genre]

		def _filter(movie):
			if any([d.lower() in movie["Genre"].lower() for d in genre]):
				return True
			return False

		self.movies = {k:v for k,v in self.movies.iteritems() if _filter(v)}

	def sort_movies(self, key="imdbRating", reverse=True):
		self.movies = sorted(self.movies.items(), key=lambda(x,y): y[key], reverse=reverse)

	def dump_to_file(self):
		with open("movielist.csv", "wb") as f:
			csvwriter = csv.writer(f, delimiter="|")
			csvwriter.writerow(["Title",
								"Year",
								"Genre",
								"IMDB rating",
								"Index"])

			for m in self.movies:
				csvwriter.writerow([m[0],
									m[1]["Year"],
									m[1]["Genre"],
									m[1]["imdbRating"],
									m[1]["Index"]])

	def process_index(self):
		for title in self.get_titles_from_index():
			self.save_imdb_record(title)

	def what_to_watch(self):
		for index in self.indexes:
			self.curIndex = index
			self.process_index()
		self.filter_by_genre()
		self.sort_movies()
		self.dump_to_file()

if __name__ == "__main__":
	indexes = [	
				"http://onad.ventures/files/tv/",
				"http://sv1.bia2dl.xyz/Series/"
			]

	m = MovieIndex(indexes)
	m.what_to_watch()
