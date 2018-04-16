#!/usr/bin/env python3
# SI507 Winter 2018 Final project
from bs4 import BeautifulSoup
import csv
import requests
import sqlite3
import secrets
import json
import plotly.plotly as py
from plotly.graph_objs import *

DBNAME = 'NBA_stats.db'
team_name={
	"ATL": "Atlanta Hawks",
	"BOS": "Boston Celtics",
	"BKN": "Brooklyn Nets",
	"CHA": "Charlotte Hornets",
	"CLE": "Cleveland Cavaliers",
	"DAL": "Dallas Mavericks",
	"DEN": "Denver Nuggets",
	"DET": "Detroit Pistons",
	"GSW": "Golden State Warriors",
	"HOU": "Houston Rockets",
	"IND": "Indiana Pacers",
	"LAC": "Los Angeles Clippers",
	"LAL": "Los Angeles Lakers",
	"MEM": "Memphis Grizzlies",
	"MIA": "Miami Heat",
	"MIL": "Milwaukee Bucks",
	"MIN": "Minnesota Timberwolves",
	"NOP": "New Orleans Pelicans",
	"NYK": "New York Knicks",
	"OKC": "Oklahoma City Thunder",
	"ORL": "Orlando Magic",
	"PHI": "Philadelphia 76ers",
	"PHX": "Phoenix Suns",
	"POR": "Portland Trail Blazers",
	"SAC": "Sacramento Kings",
	"SAS": "San Antonio Spurs",
	"TOR": "Toronto Raptors",
	"UTAH": "Utah Jazz",
	"WAS": "Washington Wizards"    
  }

# Create database and tables
def createDatabase():
	try:
		conn = sqlite3.connect(DBNAME)
		cur = conn.cursor()
	except:
		print('Unable to connect the database.')

	createTeams = '''
			CREATE TABLE 'Teams' (
				'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
				'Name' TEXT NOT NULL,
				'ArenaLocation_lat' TEXT NOT NULL,
				'ArenaLocation_lng' TEXT NOT NULL,
				'url' TEXT NOT NULL
				);
			'''
			
	createPlayers = '''
			CREATE TABLE 'Players' (
				'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
				'No' INTEGER NOT NULL,
				'url' TEXT NOT NULL,
				'Name' TEXT NOT NULL,
				'Position' TEXT,
				'Age' TEXT,
				'Height' TEXT,
				'Weight' TEXT,
				'College' TEXT,
				'TeamId' TEXT NOT NULL,
				'TeamPlayed' TEXT,
				FOREIGN KEY('TeamId') REFERENCES Teams(Id)
			);
		'''

	createRoutes = '''
			CREATE TABLE 'Routes' (
				'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
				'TeamId' TEXT NOT NULL,
				'Team1' TEXT NOT NULL,
				'Team2' TEXT NOT NULL,
				'Team3' TEXT NOT NULL,
				'Team4' TEXT NOT NULL,
				'Team5' TEXT NOT NULL,
				FOREIGN KEY('TeamId') REFERENCES Teams(Id)
			);
		'''

	createPoints = '''
			CREATE TABLE 'Points' (
				'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
				'PlayerId' TEXT NOT NULL,
				'Score1' TEXT,
				'Score2' TEXT,
				'Score3' TEXT,
				'Score4' TEXT,
				'Score5' TEXT,
				FOREIGN KEY('PlayerId') REFERENCES Players(Id)
			);
		'''
	cur.execute("DROP TABLE IF EXISTS 'Teams';")
	cur.execute("DROP TABLE IF EXISTS 'Players';")
	cur.execute("DROP TABLE IF EXISTS 'Routes';")
	cur.execute("DROP TABLE IF EXISTS 'Points';")
	cur.execute(createTeams)
	cur.execute(createPlayers)
	cur.execute(createRoutes)
	cur.execute(createPoints)
	conn.commit()
	conn.close()

# Get names, arena location, webpage url for all NBA teams
# Return a list of team names
def get_all_teams():
	teams = []
	try:
		conn = sqlite3.connect(DBNAME)
		cur = conn.cursor()
	except:
		print('Unable to connect the database.')
	
	data = {}
	CACHE_FNAME = 'NBA_teams.json'
	try:
		cache_file = open(CACHE_FNAME, 'r')
		cache_contents = cache_file.read()
		data = json.loads(cache_contents)
		cache_file.close()
	except:
		pass
		#print('No cached file!')
		
	teams = []
	if len(data) == 0:
		createDatabase()
		print("Making a request for new data for all NBA teams...")

		url = "http://www.espn.com/nba/teams"
		page = requests.get(url)
		soup = BeautifulSoup(page.text,'html.parser')
		head = soup.find_all(class_='bi')
		for t in head:
			lat = 0
			lng = 0
			name = t.text
			url = t['href']
			teams.append(name)
			data[name] = {}

			key = secrets.google_places_key
			search_url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?query='+name+'+arena'+'&key='+key

			search = requests.get(search_url)
			loc_res = json.loads(search.text)
			
			if len(loc_res['results'])>0:
				lat = loc_res['results'][0]['geometry']['location']['lat']
				lng = loc_res['results'][0]['geometry']['location']['lng']
				data[name]['lat']=lat
				data[name]['lng']=lng
				data[name]['url']=url

			insertion = (name,lat,lng,url)
			statement = 'INSERT INTO Teams '
			statement += 'VALUES (NULL, ?, ?, ?, ?)'

			cur.execute(statement, insertion)
			conn.commit()

			fw = open(CACHE_FNAME,"w")
			json.dump(data,fw, indent=4)
			fw.close()
	else:
		print("Getting cached data for all NBA teams...")
		for r in data:
			teams.append(r)
	
	conn.close()	
	return teams

# Get all players for a team
def get_players(team):
	name = []
	try:
		conn = sqlite3.connect(DBNAME)
		cur = conn.cursor()
	except:
		print('Unable to connect the database.')

	data = {}
	CACHE_FNAME = 'players.json'
	try:
		cache_file = open(CACHE_FNAME, 'r')
		cache_contents = cache_file.read()
		data = json.loads(cache_contents)
		cache_file.close()
	except:
		
		print('No cached file!')

	if team in data:
		for p in data[team]:
			#print(p)
			name.append(p) 
	
	# try:
	# 	statement = 
	# 		SELECT p.Name FROM Teams as t
	# 			JOIN Players as p
	# 			ON p.TeamId = t.Id
	# 		WHERE t.Name=?
		
	# 	params = (team,)
	# 	res = cur.execute(statement,params)
	# 	results = res.fetchall()
	# 	tmp=results[0]
			
	# except:
	else:
		
		data[team] = {}
		statement = 'SELECT Id, url FROM Teams WHERE Name="'+team+'"'
		tmp=cur.execute(statement)
		res=tmp.fetchone()
		teamId = res[0]
		url = res[1].split('_')[0]+'roster/_'+res[1].split('_')[1]
		#print(url)
		page = requests.get(url)
		soup = BeautifulSoup(page.text,'html.parser')
		head = soup.find(class_="tablehead")
		player = head.find_all('tr')
	
		for i,t in enumerate(player):
			pl = []
			if i >= 2:
				td=t.find_all('td')
				for j,c in enumerate(td):
					if j<=6:
						if j==1:
							pl.append(c.find('a')['href'])
							pl.append(c.text)

						else:				
							pl.append(c.text)
				#print(pl)
				insertion = (pl[0],pl[1],pl[2],pl[3],pl[4],pl[5],pl[6],pl[7],teamId)
				statement = 'INSERT INTO Players '
				statement += 'VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)'

				cur.execute(statement, insertion)
				conn.commit()

				name.append(pl[2])
				data[team][pl[2]]={}
				data[team][pl[2]]['url']=pl[1]
				data[team][pl[2]]['position']=pl[3]
				data[team][pl[2]]['age']=pl[4]
				data[team][pl[2]]['height']=pl[5]
				data[team][pl[2]]['weight']=pl[6]
				data[team][pl[2]]['college']=pl[7]
				fw = open(CACHE_FNAME,"w")
				json.dump(data,fw, indent=4)
				fw.close()

	conn.close()
	return name

# Get previous 5 games results for a team
def get_team_route(team):
	try:
		conn = sqlite3.connect(DBNAME)
		cur = conn.cursor()
	except:
		print('Unable to connect the database.')

	data = {}
	CACHE_FNAME = 'routes.json'
	try:
		cache_file = open(CACHE_FNAME, 'r')
		cache_contents = cache_file.read()
		data = json.loads(cache_contents)
		cache_file.close()
	except:
		pass
		#print('No cached file!')

	statement = 'SELECT Id, url FROM Teams WHERE Name="'+team+'"'
	tmp=cur.execute(statement)
	res=tmp.fetchone()
	teamId = res[0]
	url = res[1]
	page = requests.get(url)
	soup = BeautifulSoup(page.text,'html.parser')
	head = soup.find(class_="club-schedule")
	game = head.find_all('li')
	rival = [team]
	count=0
	for li in game:
		#print(li)
		if count != 0 and count < 6:
			against=li.find(class_="game-info").text
			score=li.find(class_="score").text
			res=li.find(class_="game-result").text
			rival.append(against+' '+res+' '+score)		
		count+=1
	#print(len(rival))

	#try:
	if team in data:
		'''
		statement = 
			SELECT * FROM Routes as r
				JOIN Teams as t
				ON t.Id = r.TeamId
			WHERE t.Name=?
		
		params = (team,)
		res = cur.execute(statement,params)
		tmp=res.fetchone()[0]
		'''
		
		update = (rival[1],rival[2],rival[3],rival[4],rival[5],teamId)
		statement = '''
			UPDATE Routes
			SET Team1=?,
				Team2=?,
				Team3=?,
				Team4=?,
				Team5=?
			WHERE teamId=?
		'''
		cur.execute(statement, update)
		conn.commit()

		data[team]['team1']=rival[1]
		data[team]['team2']=rival[2]
		data[team]['team3']=rival[3]
		data[team]['team4']=rival[4]
		data[team]['team5']=rival[5]

	#except:
	else:
		insertion = (teamId,rival[1],rival[2],rival[3],rival[4],rival[5])
		statement = 'INSERT INTO Routes '
		statement += 'VALUES (NULL, ?, ?, ?, ?, ?, ?)'

		cur.execute(statement, insertion)
		conn.commit()

		data[team]={}
		data[team]['team1']=rival[1]
		data[team]['team2']=rival[2]
		data[team]['team3']=rival[3]
		data[team]['team4']=rival[4]
		data[team]['team5']=rival[5]

	fw = open(CACHE_FNAME,"w")
	json.dump(data,fw, indent=4)
	fw.close()

	conn.close()
	return rival

# Get points of a player in previous 5 games
def get_points(player):
	try:
		conn = sqlite3.connect(DBNAME)
		cur = conn.cursor()
	except:
		print('Unable to connect the database.')

	data = {}
	CACHE_FNAME = 'points.json'
	try:
		cache_file = open(CACHE_FNAME, 'r')
		cache_contents = cache_file.read()
		data = json.loads(cache_contents)
		cache_file.close()
	except:
		pass
		#print('No cached file!')


	statement = '''
			SELECT url FROM Players 
			WHERE Name=?
		'''
	params = (player,)
	result = cur.execute(statement,params)
	url = result.fetchone()[0]
	#print(url)

	points = []
	page = requests.get(url)
	soup = BeautifulSoup(page.text,'html.parser')
	head = soup.find_all(class_="tablehead")
	for i,t in enumerate(head):
		if i == 2:
			table=t.find_all('tr')
			for k,tr in enumerate(table):
				if k < 6:
					against=''
					td = tr.find_all('td')
					for j,d in enumerate(td):
						
						if j == 1:
							against=d.text
						if j == len(td)-1:
							p=d.text
					if against:
						points.append(against+' '+p)
	
	#try:
	if player in data:
		statement = '''
			SELECT p.Id 
			FROM Players as p
				JOIN Points as o
				ON p.Id=o.PlayerId
			WHERE p.Name=?
		'''
		params = (player,)
		res = cur.execute(statement,params)
		playerId=res.fetchone()[0]
		#print(playerId)
		update = (points[0],points[1],points[2],points[3],points[4],playerId)
		statement = '''
			UPDATE Points
			SET Score1=?,
				Score2=?,
				Score3=?,
				Score4=?,
				Score5=?
			WHERE PlayerId=?
		'''
		cur.execute(statement, update)
		conn.commit()

		data[player]['score1']=points[0]
		data[player]['score2']=points[1]
		data[player]['score3']=points[2]
		data[player]['score4']=points[3]
		data[player]['score5']=points[4]

	#except:
	else:
		statement = '''
			SELECT Id FROM Players
			WHERE Name=?
		'''
		params = (player,)
		res = cur.execute(statement,params)
		playerId=res.fetchone()[0]

		insertion = (playerId,points[0],points[1],points[2],points[3],points[4])
		statement = 'INSERT INTO Points '
		statement += 'VALUES (NULL, ?, ?, ?, ?, ?, ?)'

		cur.execute(statement, insertion)
		conn.commit()

		data[player]={}
		data[player]['score1']=points[0]
		data[player]['score2']=points[1]
		data[player]['score3']=points[2]
		data[player]['score4']=points[3]
		data[player]['score5']=points[4]

	fw = open(CACHE_FNAME,"w")
	json.dump(data,fw, indent=4)
	fw.close()

	conn.close()
	return points

# Get teams a player've ever played for
def get_preteam(player):
	try:
		conn = sqlite3.connect(DBNAME)
		cur = conn.cursor()
	except:
		print('Unable to connect the database.')

	statement = '''
			SELECT url FROM Players 
			WHERE Name=?
		'''
	params = (player,)
	result = cur.execute(statement,params)
	res = result.fetchone()
	#print(res)
	url = res[0].split('_')[0]+'stats/_'+res[0].split('_')[1]

	team = []
	page = requests.get(url)
	soup = BeautifulSoup(page.text,'html.parser')
	head = soup.find_all(class_="team-name")
	for li in head:
		if li.text not in team:
			team.append(li.text)
	
	update = ('_'.join(team),player)
	statement = '''
		UPDATE Players
		SET TeamPlayed=?
		WHERE Name=?
	'''
	cur.execute(statement, update)
	conn.commit()
	conn.close()
	return team

# Plot the location for all NBA teams
def plot_all_teams():
	try:
		conn = sqlite3.connect(DBNAME)
		cur = conn.cursor()
	except:
		print('Unable to connect the database.')

	lat_vals = []
	lon_vals = []
	text_vals = []

	statement = 'SELECT Name, ArenaLocation_lat, ArenaLocation_lng FROM Teams'
	tmp=cur.execute(statement)
	res=tmp.fetchall()

	for t in res:
		lat_vals.append(t[1])
		lon_vals.append(t[2])
		text_vals.append(t[0])

	team_loc = [dict(
			type = 'scattergeo',
			locationmode = 'USA-states',
			lon = lon_vals,
			lat = lat_vals,
			text = text_vals,
			mode = 'markers',
			marker = dict(
				size = 8,
				symbol = 'circle',
				color = 'red'
			))]

	layout = dict(
			title = 'Arena Locations of all NBA teams',
			geo = dict(
				scope='usa',
				projection=dict( type='albers usa' ),
				showland = True,
				landcolor = "rgb(250, 208, 89)",
				subunitcolor = "rgb(234, 236, 235)",
				countrycolor = "rgb(0, 208, 89)",
				#lataxis = {'range': lat_axis},
				#lonaxis = {'range': lon_axis},
				#center= {'lat': center_lat, 'lon': center_lon },
				countrywidth = 3,
				subunitwidth = 3
			),
		)

	fig = dict(data=team_loc, layout=layout )
	py.plot( fig, validate=False, filename='all_teams')       

	conn.close()

# Plot game route for a team
def plot_game_route(rival):
	try:
		conn = sqlite3.connect(DBNAME)
		cur = conn.cursor()
	except:
		print('Unable to connect the database.')

	lat_vals_win = []
	lon_vals_win = []
	lat_vals_lose = []
	lon_vals_lose = []
	text_vals_win = []
	text_vals_lose = []

	for i in range(1,len(rival)):
		home = False
		if rival[i].startswith('vs'):
			team=rival[0]
			home =True
		else:
			#print(rival[i].split(' '))
			team=rival[i].split(' ')[2]
		statement = 'SELECT Name, ArenaLocation_lat, ArenaLocation_lng FROM Teams WHERE Name LIKE "%'+team+'%"'
		tmp=cur.execute(statement)
		res=tmp.fetchone()
		
		if home:
			lat = str(float(res[1])+i*0.1)
			lon = str(float(res[2])+i*0.1)
		else:
			lat = res[1]
			lon = res[2]
		
		if rival[i].split(' ')[2] == 'W' or rival[i].split(' ')[3] == 'W':
			lat_vals_win.append(lat)
			lon_vals_win.append(lon)
			text_vals_win.append(rival[i])

		else:
			lat_vals_lose.append(lat)
			lon_vals_lose.append(lon)
			text_vals_lose.append(rival[i])

	win_trace = dict(
				type = 'scattergeo',
				locationmode = 'USA-states',
				lon = lon_vals_win,
				lat = lat_vals_win,
				text = text_vals_win,
				mode = 'markers',
				marker = dict(
					size = 20,
					symbol = 'star',
					color = 'green'
				))

	lose_trace = dict(
			type = 'scattergeo',
			locationmode = 'USA-states',
			lon = lon_vals_lose,
			lat = lat_vals_lose,
			text = text_vals_lose,
			mode = 'markers',
			marker = dict(
				size = 8,
				symbol = 'circle',
				color = 'red'
			))
	plot_data = [win_trace, lose_trace]

	layout = dict(
			title = 'Past 5 game routes for '+rival[0],
			geo = dict(
				scope='usa',
				projection=dict( type='albers usa' ),
				showland = True,
				landcolor = "rgb(250, 208, 89)",
				subunitcolor = "rgb(234, 236, 235)",
				countrycolor = "rgb(0, 208, 89)",
				#lataxis = {'range': lat_axis},
				#lonaxis = {'range': lon_axis},
				#center= {'lat': center_lat, 'lon': center_lon },
				countrywidth = 3,
				subunitwidth = 3
			),
		)

	fig = dict(data=plot_data, layout=layout )
	py.plot( fig, validate=False, filename='team_route')       

	conn.close()

# Plot teams a player've ever played for
def plot_team_played(team):
	try:
		conn = sqlite3.connect(DBNAME)
		cur = conn.cursor()
	except:
		print('Unable to connect the database.')

	lat_vals_old = []
	lon_vals_old = []
	text_vals_old = []
	lat_vals_now = []
	lon_vals_now = []
	text_vals_now = []

	for i,t in enumerate(team):
		name = team_name[t]
		statement = '''
			SELECT Name, ArenaLocation_lat, ArenaLocation_lng 
			FROM Teams
			WHERE Name=?
		'''
		params = (name,)
		tmp=cur.execute(statement,params)
		res=tmp.fetchone()
		print(res)

		if i == len(team)-1:
			lat_vals_now.append(res[1])
			lon_vals_now.append(res[2])
			text_vals_now.append(res[0])
		else:
			lat_vals_old.append(res[1])
			lon_vals_old.append(res[2])
			text_vals_old.append(res[0])

	now_trace = dict(
				type = 'scattergeo',
				locationmode = 'USA-states',
				lon = lon_vals_now,
				lat = lat_vals_now,
				text = text_vals_now,
				mode = 'markers',
				marker = dict(
					size = 20,
					symbol = 'star',
					color = 'green'
				))

	old_trace = dict(
			type = 'scattergeo',
			locationmode = 'USA-states',
			lon = lon_vals_old,
			lat = lat_vals_old,
			text = text_vals_old,
			mode = 'markers',
			marker = dict(
				size = 8,
				symbol = 'circle',
				color = 'red'
			))
	plot_data = [now_trace, old_trace]

	layout = dict(
			title = 'Teams ever played for ',
			geo = dict(
				scope='usa',
				projection=dict( type='albers usa' ),
				showland = True,
				landcolor = "rgb(250, 208, 89)",
				subunitcolor = "rgb(234, 236, 235)",
				countrycolor = "rgb(0, 208, 89)",
				countrywidth = 3,
				subunitwidth = 3
			),
		)

	fig = dict(data=plot_data, layout=layout )
	py.plot( fig, validate=False, filename='team_played')       
  
# Plot histogram for points in last 5 game
def plot_point(point):
	'''
	try:
		conn = sqlite3.connect(DBNAME)
		cur = conn.cursor()
	except:
		print('Unable to connect the database.')

	statement = 
			SELECT Score1,Score2,Score3,Score4,Score5 
			FROM Points as o
				JOIN Players as p
				ON p.Id=o.PlayerId
			WHERE p.Name=?
		
	params = (player,)
	result = cur.execute(statement,params)
	res = result.fetchone()
	'''
	points=[]
	team=[]
	for r in point:
		if r.startswith('vs'):
			points.append(r.split(' ')[1])
			team.append(r.split(' ')[0])
		else:
			points.append(r.split(' ')[2])
			team.append(r.split(' ')[0]+' '+r.split(' ')[1])
	
	data=Data([{'y':points,
				'x':team,
				"marker": {"color": "blue", "size": 12},
				"mode": "markers",
				"type": "scatter"}])
	layout = {"title": "Points in past 5 games", 
		  "xaxis": {"title": "Games", }, 
		  "yaxis": {"title": "Points"}}

	fig = dict(data=data, layout=layout)
	py.plot( fig, validate=False, filename='point')       
	
	#conn.close()
	
if __name__ == '__main__':
	#createDatabase()
	route = ['Boston Celtics','vs  Grizzlies W 113-98','@  Trail Blazers W 97-95','@  Nuggets L 88-82']
	#get_all_teams()
	#plot_all_teams()
	#get_team_route('Boston Celtics')
	#print(rival)
	#rival = ['Raptors','Jazz','Suns']
	plot_game_route(route)
	#get_players('Utah Jazz')
	#team=['DAL','BOS','CLE','UTAH']
	#plot_team_played(team)
	#a=get_points('Kyrie Irving')
	#plot_point(a)

'''
	team = []
	player = []
	route = []
	point = []
	preteam = []

	user_input = str(input('\nEnter command (or "help" for options): '))
	while user_input != 'exit':
		
		if 'help' in user_input: 
			print(
	list 
		available anytime
		lists all teams in the NBA league
		inputs: no input needed
	route <result_number> 
		available only if there is an active team list set
		lists routes for that team in past 5 games
		valid inputs: an integer 1-len(result_set_size)
	player <result_number>
		available only if there is an active team list set
		lists all players in that NBA team
		valid inputs: an integer 1-len(result_set_size)
	point <result_number> 
		available only if there is an active player list set
		lists points for that player in past 5 games
		valid inputs: an integer 1-len(result_set_size)
	preteam <result_number>
		available only if there is an active player list set
		lists teams a player've ever played for
		valid inputs: an integer 1-len(result_set_size)
	map <data_type>
		available only if there is an active result set
		displays the current results of choosen data type on a map
		valid inputs: team, route, point, preteam
	exit
		exits the program 
	help
		lists available commands (these instructions))  
		elif user_input == 'list':
			player = []
			route = []
			point = []
			preteam = []
			team = get_all_teams()
			for i,t in enumerate(team):
				print(i+1, t)

		elif user_input.startswith('route'):
			try:
				idx = int(user_input.split()[1])
				if len(team)>0 and idx>0 and idx<=len(team):
					target = team[idx-1]
					print('\nRoutes for '+target+' in past 5 games:')
					route = get_team_route(target)
					if len(route)>0:
						for i,r in enumerate(route):
							if i > 0:
								print(i,r)
				else:
					print('No route result for team '+target+'!')
			except:
				print('Please enter an int for a team!')

		elif user_input.startswith('player'):
			try:            
				idx = int(user_input.split()[1])
				if len(team)>0 and idx>0 and idx<=len(team):
					target = team[idx-1]
					print('\nPlayers in '+target)
					player = get_players(target)
					if len(player)>0:
						for i,p in enumerate(player):
							print(i+1,p)
				else:
					print('No player result for team '+target+'!')
			except:
				print('Please enter an int for the team!')

		elif user_input.startswith('point'):
			try:
				idx = int(user_input.split()[1])
				if len(player)>0 and idx>0 and idx<=len(player):
					pla = player[idx-1]
					print('\nPoints for '+pla+' in past 5 games:')
					point = get_points(pla)
					if len(point)>0:
						for i,p in enumerate(point):
							print(i+1,p)
				else:
					print('No point result for player '+pla+'!')
			except:
				print('Please enter an int for a player!')

		elif user_input.startswith('preteam'):
			try:
				idx = int(user_input.split()[1])
				if len(player)>0 and idx>0 and idx<=len(player):
					pla = player[idx-1]
					print('\nTeams '+pla+' ever played for:')
					preteam = get_preteam(pla)
					if len(preteam)>0:
						for i,t in enumerate(preteam):
							print(i+1,t)
				else:
					print('No point result for player '+pla+'!')
			except:
				print('Please enter an int for a player!')

		elif user_input.startswith('map'):
			try:
				choosenType = str(user_input.split()[1])
				if len(team)>0 and choosenType=='team':
					plot_all_teams()
					print('\nOpened a web page for '+choosenType+'!')
				elif len(route)>0 and choosenType=='route':
					plot_game_route(route)
					print('\nOpened a web page for '+choosenType+'!')
				elif len(point)>0 and choosenType=='point':
					plot_point(point)
					print('\nOpened a web page for '+choosenType+'!')
				elif len(preteam)>0 and choosenType=='preteam':
					plot_team_played(preteam)
					print('\nOpened a web page for '+choosenType+'!')
				else:
					print('No map result for data '+choosenType+'!')
			except:
				print('Please enter a valid data for a visualization!')

			

		else:
			print('Invalid user input!')

		user_input = str(input('\nEnter command (or "help" for options): '))

	print('Bye!')
'''
