import BabyHomeCrawler as BHCrawler
import time

def main():
    answer = input(u'Want to update Topic Tree? (see topic_tree.txt) [yes/no]:')
    if answer.lower() == 'yes':
        code2link = BHCrawler.UpdateTopicTree('https://forum.babyhome.com.tw')
    elif answer.lower() == 'no':
        code2link = BHCrawler.ReadTopicTree()

    code = input(u'Which topic code would you want to crawl? (see topic_tree.txt):')
    if code in code2link:
        TOPIC = code2link[code][1]
        TOPIC_URL = code2link[code][0]

        year_want_to_crawl = input(u'Want to crawl to posts within how many years? [1/3/5/all]:')

        TOPIC_URL = TOPIC_URL + '?year=' + year_want_to_crawl

        total_page_num = BHCrawler.GetTotalPageNum(TOPIC_URL)
        print(u'Topic <{}> has {} pages within {} years.'.format(TOPIC, total_page_num, year_want_to_crawl))

        page_want_to_crawl = input(u'How many pages do you want to crawl? ')
        # if the input is valid (negative number, string, input nothing)
        if page_want_to_crawl == '' or not page_want_to_crawl.isdigit() or int(page_want_to_crawl) <= 0:
            print('EXIT')
        else:
            page_want_to_crawl = min(int(page_want_to_crawl), total_page_num)
            print('====================')
            print(u'Topic: {}\nTime: within {} years\nPages: {}'.format(TOPIC, year_want_to_crawl, page_want_to_crawl))
            
            start = time.time()
            
            pages_link = list()
            for i in range(1, page_want_to_crawl + 1):
                url = TOPIC_URL + '&page=' + str(i)
                pages_link.append(url)

            posts = BHCrawler.GetPosts(pages_link)
            print(u'{} posts in total'.format(len(posts)))

            posts_data = BHCrawler.GetArticles(posts)
            
            print(u'Spend {} seconds on crawling.'.format(time.time()-start))

            ans = input('Save to database? [yes/no]:')
            if ans.lower() == 'yes':
                BHCrawler.Save2DB('data.db', posts_data)

    else:
        print(u'Topic code doesn\'t exist. Please check topic_tree.txt')

if __name__ == '__main__':
    main()