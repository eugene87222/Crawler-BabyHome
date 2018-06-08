import warnings
warnings.filterwarnings('ignore')

import requests
import sqlite3
from bs4 import BeautifulSoup
from multiprocessing import Pool

##########################################
# get the html code with given url       #
# param: full_url -> url of the web page #
##########################################
def GetPageContent(url):
	res = requests.get(url)
	content = BeautifulSoup(res.text)
	return content

########################################
# get the page number of the topic     #
# param: TOPIC_URL -> url of the topic #
########################################
def GetTotalPageNum(TOPIC_URL):
	content = GetPageContent(TOPIC_URL)
	content = content.findAll('ul', {'class':'pagination'})[0]
	content = content.findAll('li')[-1]

	url = content.find('a')['href']

	content = GetPageContent(url)
	content = content.findAll('ul', {'class':'pagination'})[0]
	content = content.findAll('li')[-1]

	return int(content.text)

################################################
# build the topic tree                         #
# param: file_tree -> file object (topic tree) #
#        file_link -> file object (code2link)  #
################################################
def BuildTopicTree(file_tree, file_link, topic, tier, code, stop):
	code2link = dict()

	cates = GetPageContent(topic.find('a')['href'])
	cates = cates.findAll('li', {'role':'presentation'})

	forums = [cate.text for cate in cates]

	string = ''

	if topic.text in forums:
		stop = True
	for i in range(tier):
		string += '  '
	if tier:
		string += '|== '

	string = string + topic.text + ' ' + code
	print (string)

	file_tree.write(string + '\n')
	file_link.write(code + ' ' + topic.find('a')['href'] + ' ' + topic.text + '\n')
	
	code2link[code] = topic.find('a')['href']
	
	i = 1
	if len(cates):
		if not stop:
			for cate in cates:
				# build the topic tree recursively
				code2link = {**code2link, **BuildTopicTree(file_tree, file_link, cate, tier + 1, code + '-' + str(i), stop)}
				i += 1
	
	return code2link

################################################
# update the topic tree                        #
# see topic_tree.txt and code2link.txt         #
################################################
def UpdateTopicTree(url):
	content = GetPageContent(url)

	cates = content.findAll('p', {'class':'main-section'})

	file_tree = open('topic_tree.txt', 'w', encoding='utf-8')
	file_link = open('code2link.txt', 'w', encoding='utf-8')

	code2link = dict()

	i = 1
	for cate in cates:
		code2link = {**code2link, **BuildTopicTree(file_tree, file_link, cate, 0, str(i), False)}
		i += 1

	file_tree.close()
	file_link.close()
	
	return code2link

########################################
# read the topic tree file             #
# see topic_tree.txt and code2link.txt #
########################################
def ReadTopicTree():
	file = open('code2link.txt', 'r', encoding='utf-8')

	code2link = dict()
	for line in file:
		read = line.rstrip()
		parse = read.split(' ')
		code2link[parse[0]] = [parse[1], parse[2]]

	file.close()

	file = open('topic_tree.txt', 'r', encoding='utf-8')
	for line in file:
		print (line, end='')

	file.close()

	return code2link

######################################################
# get the meta data of each post in a post list page #
# param: url -> url of post list page               #
######################################################
def ParseGetMetaData(url):
	content = GetPageContent(url)

	shift = content.findAll('div', {'class':'sidebar-span'})
	if shift:
		for elem in shift:
			elem = elem.extract()

	rows = content.findAll('li', {'class':'media'})
	
	posts = list()
	for row in rows:
		meta = row.find('div', {'class':'media-body'})
		if meta:
			posts.append({
				'link': meta.find('p', {'class':'media-heading'}).find('a')['href'],
				'title': meta.find('p', {'class':'media-heading'}).text,
				'author': row.find('div', {'class':'user-name'}).text.lstrip(),
				'reply': meta.find('a', {'class':'comments'}).text
			})

	return posts

#######################################################
# get the meta data of all the posts                  #
# param: pages_link -> url of post list page (a list) #
#######################################################
def GetPosts(pages_link):
	with Pool(4) as p:
		post_list = p.map(ParseGetMetaData, pages_link)
	
	all_post_list = list()
	
	for each_page in post_list:
		for each_post in each_page:
			all_post_list.append(each_post)
	
	return all_post_list

#################################
# get the article of the post   #
# param: url -> url of the post #
#################################
def ParseGetArticle(url):
	content = GetPageContent(url)
	content = content.findAll('div', {'class':'media-body'})[1]

	date = content.find('p', {'class':'floors'})

	shift = date.findAll(['span', 'a'])
	if shift:
		for elem in shift:
			elem = elem.extract()

	date = date.text.rstrip()

	article = content.find('div', {'class':'thread-inner'})
	shift = article.find('div', {'class':'thread-options'})
	if shift:
		shift = shift.extract()

	article = article.text.lstrip().rstrip()

	return {'date': date, 'content': article}

#########################################
# get the articles of each post         #
# param: post_link -> urls of all posts #
#########################################
def GetArticles(post_list):
	post_link = [entry['link'] for entry in post_list]

	all_post_content = list()

	with Pool(4) as p:
		contents = p.map(ParseGetArticle, post_link)

	for i in range(len(post_list)):
		all_post_content.append({
			'title': post_list[i]['title'], 
			'link': post_list[i]['link'], 
			'date': contents[i]['date'],
			'author': post_list[i]['author'], 
			'reply': post_list[i]['reply'], 
			'content': contents[i]['content']
		})

	return all_post_content

##########################################
# save data into SQLite database         #
# param: db_name -> name of the database #
#        posts -> posts data             #
##########################################
def Save2DB(db_name, posts):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    create_table = """ CREATE TABLE IF NOT EXISTS table1(
    					ID integer PRIMARY KEY,
    					title text NOT NULL,
                        link text NOT NULL,
                        date text NOT NULL,
                        author text NOT NULL,
                        reply text NOT NULL,
                        content text NOT NULL
                        ); """
    cur.execute(create_table)
    for i in posts:
        cur.execute("insert into table1 (title, link, date, author, reply, content) values (?, ?, ?, ?, ?, ?)",
            (i['title'], i['link'], i['date'], i['author'], i['reply'], i['content']))
    conn.commit()
    conn.close()