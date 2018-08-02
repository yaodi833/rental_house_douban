# coding:utf-8
import requests,json,time
import smtplib
from email.mime.text import MIMEText
import random


# nohup stdbuf -oL python group_api_topics.py &
mailto_list = ['296840029@qq.com', '330979050@qq.com']
mail_host = "smtp.qq.com"
mail_user = "330979050@qq.com"
mail_pass = "****************"
mail_postfix = "qq.com"

sended_dict = {}
px_pool = []

# 发送邮件到指定邮箱，其中mailuser 为发送邮件邮箱账号， mailto_list 为接收邮件账户列表
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

# 由于豆瓣api限制，每小时只能发送100个请求，此函数为程序加载不同Https代理，每次请求随机选择不同的https代理
def load_proxy_pool():
    for l in open('./proxy_pool','r').readlines():
        px = l.split('\n')[0].split('\t')
        px_pool.append('https://{}:{}'.format(px[0],px[1]))
    print px_pool



#此函数发送 get 请求， params为请求参数，指定从何处开始，每次请求要求返回多少条消息
#返回消息为json格式，具体属性名称及格式参考 https://www.douban.com/group/topic/33507002/

def get_topic_list(groupids= ['beijingzufang']):

    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/52.0.2743.116 Safari/537.36'}
    params = {'start': 0, 'count': 150}
    print '-------------------'
    topics = []
    for id in groupids:
        flag = True
        r = None
        while flag:
            proxies = {'https': random.choice(px_pool)}
            print 'groupid: {}, proxy:{}'.format(id, proxies)
            try:
                r = requests.get('https://api.douban.com/v2/group/{}/topics'.format(id),
                                 headers = headers,
                                 proxies = proxies,
                                 params = params)
                if r.status_code == 200:
                    flag = False
                else:
                    print ('Bad proxy:', proxies)
            except Exception, e:
                print ('Error proxy:', proxies)
                print str(e)

        data = json.loads(r.text)
        print data['topics'][0]['updated']
        print data['topics'][-1]['updated']
        topics.extend(data['topics'])
    print '-------------------'
    print 'Save json files'
    json_obj = {"data": topics}
    save_json_file(json_obj)
    return topics

# 搜索topic内容中是否包含 指定关键字的topic
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
# 遍历所有在topics 中的topic， 找到含有关键词列表keywords 的所有topic 并返回
def related_houses(topics, keywords = []):
    houses = []
    for topic in topics:
        url = content_search(topic, keywords)
        if url is not None:
            houses.append(url)
    return houses

# 此函数为检测相同的topic是否已发送过， 如果发送过则不发送， 没有发送过则发送并在发送过的字典中添加该topic
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

# 此函数为加载是否历史发送过的topic 列表，初始时为空， 每次发送都重新写入
def recovery_sendedurls():
    content = open('./sended_urls', 'r').readline()
    if content != '':
        strs = eval(content)
        if strs is not None :
            for i in strs:
                sended_dict[i] = ''
    print sended_dict.keys()

# 此函数为监控的主函数，每隔gap秒对小组列表内的小组发送一次请求，
# 如果返回结果中不含有满足要求topic， 即len(f_houses)=0 则不发送邮件
# 如果含有满足要求的topic 则发送邮件
def topic_monitor(gap = 420, keywords = [], groupids = []):
    while True:
        topics = get_topic_list(groupids = groupids)
        houses = related_houses(topics, keywords)
        f_houses = house_filter(houses)
        if len(f_houses)>0:
            print f_houses
            send_mail(mailto_list, 'For your information, House!', str(f_houses))
        time.sleep(gap)

def save_json_file(objs):
    f = open('./results.json','w')
    json.dump(objs, f)
    f.close()


if __name__ == '__main__':
    keywords = ['柳浪', '肖家河', '上地', '西北旺', '农大南路','农大西','永旺','大牛坊']
    groupids = ['fangzi']
    # groupids = ['fangzi','beijingzufang', 'opking', '279962','sweethome','zhufang','26926']
    recovery_sendedurls()
    load_proxy_pool()
    topic_monitor(keywords=keywords, groupids = groupids)
