# coding:utf-8
import requests,json,time
import smtplib
from email.mime.text import MIMEText
import random

mailto_list = ['XXXXXXXXXX@qq.com', 'XXXXXXXXXX@qq.com']
mail_host = "smtp.qq.com"
mail_user = "XXXXXXXXXX@qq.com"
mail_pass = "XXXXXXXXXX"
mail_postfix = "qq.com"

sended_dict = {}
px_pool = []

def send_mail(to_list, sub, content):
    me = "Server Monitor" + "<" + mail_user + "@" + mail_postfix + ">"
    msg = MIMEText(content, _subtype='plain', _charset='gb2312')
    msg['Subject'] = sub
    msg['From'] = me
    msg['To'] = ";".join(to_list)
    try:
        server = smtplib.SMTP_SSL()
        server.connect(mail_host)
        server.login(mail_user, mail_pass)
        server.sendmail(me, to_list, msg.as_string())
        server.close()
        return True
    except Exception, e:
        print str(e)
        return False


def load_proxy_pool():
    for l in open('./proxy_pool','r').readlines():
        px = l.split('\n')[0].split('\t')
        px_pool.append('https://{}:{}'.format(px[0],px[1]))
    print px_pool


def get_topic_list(groupids= ['beijingzufang']):



    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/52.0.2743.116 Safari/537.36'}

    print '-------------------'
    topics = []
    for id in groupids:
        flag = True
        r = None
        while flag:
            proxies = {'https': random.choice(px_pool)}
            print proxies
            try:
                r = requests.get('https://api.douban.com/v2/group/{}/topics'.format(id),
                                 headers = headers,
                                 proxies = proxies)
                if r.status_code == 200:
                    flag = False
                else:
                    print ('Bad proxy:', proxies)
            except Exception, e:
                print ('Error proxy:', proxies)
                print str(e)

        data = json.loads(r.text)
        topics.extend(data['topics'])
    return topics

def content_search(topic, key_words = []):
    flag = False
    for k in key_words:
        if k.decode('utf-8') in topic['title']:
            flag = True
        elif k.decode('utf-8') in topic['content']:
            flag = True
    if flag==True:
        return topic['share_url']
    else:
        return

def related_houses(topics, keywords = []):
    houses = []
    for topic in topics:
        url = content_search(topic, keywords)
        if url is not None:
            houses.append(url)
    return houses

def house_filter(houses):
    filterd_hs = []
    for h in houses:
        if not sended_dict.has_key(h):
            sended_dict[h] = ''
            filterd_hs.append(h)
            sended_urls = open('./sended_urls', 'w')
            sended_urls.write(str(sended_dict.keys()))
            sended_urls.flush()
            sended_urls.close()
    return filterd_hs

def recovery_sendedurls():
    strs = eval(open('./sended_urls', 'r').readline())
    if strs is not None:
        for i in strs:
            sended_dict[i] = ''
    print sended_dict.keys()


def topic_monitor(gap = 50, keywords = [], groupids = []):
    while True:
        topics = get_topic_list(groupids = groupids)
        houses = related_houses(topics, keywords)
        f_houses = house_filter(houses)
        if len(f_houses)>0:
            print f_houses
            send_mail(mailto_list, 'For your information, House!', str(f_houses))
        time.sleep(random.randint(gap,gap+20))

if __name__ == '__main__':
    keywords = ['柳浪', '肖家河', '上地', '西北旺', '农大南路']
    groupids = ['beijingzufang', 'opking', '279962','sweethome','zhufang','26926']
    recovery_sendedurls()
    load_proxy_pool()
    topic_monitor(keywords=keywords, groupids = groupids)
