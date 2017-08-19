#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import re, time, json, logging, hashlib, base64, asyncio,os,codecs,types

from markdown2 import Markdown
from aiohttp import web

from coroweb import get, post
COOKIE_NAME = 'wang_blog_session'
_COOKIE_KEY = "wang"


def get_user():
    user_name = "940530348@qq.com"
    user_passwd = "4cd05f15364f78fdb27c3822c93b71d37ad6ac08"
    sha1 = hashlib.sha1()
    sha1.update(user_name.encode('utf-8'))
    sha1.update(b':')
    sha1.update(user_passwd.encode('utf-8'))
    user_passwd = sha1.hexdigest()
    user={'id':user_name,'passwd':user_passwd}
    return user

def user2cookie(user, max_age):
    '''
    Generate cookie str by user.
    '''
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user['id'], user['passwd'], expires, _COOKIE_KEY)
    L = [user['id'], expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)



def cookie2user(cookie_str):
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = get_user()
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user['passwd'], expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user['passwd'] = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None


@get('/')
def index(request):
    return {
        '__template__': 'index.html',
        'index': index,
    }

@get('/contact')
def contact(request):
    return {
        '__template__': 'contact.html',
        'index': contact,
    }

@get('/help')
def help(request):
    return {
        '__template__': 'help.html',
        'help': help,
    }

@get('/help/{title2}')
def passage(title2):
    try:
        with codecs.open(os.getcwd()+'/templates/'+title2+'.md', 'r', 'utf-8') as f:
            md = f.read()
            markdowner = Markdown(extras=["fenced-code-blocks"])
            md = markdowner.convert(md)
            md = '%s'%md
    except:
        return {
            '__template__': '%s.html'%title2,
        }

    return {
        '__template__': 'passage.html',
        'md' : md,
    }
@get('/study')
def study(request):
    with codecs.open(os.getcwd()+'/templates/'+'study.md', 'r', 'utf-8') as f:
        md = f.read()
        markdowner = Markdown(extras=["fenced-code-blocks"])
        md = markdowner.convert(md)
        md = '%s'%md

    return {
        '__template__': 'study.html',
        'md' : md,
    }
@get('/manage')
def manage(request):
    arrayy=[]
    with codecs.open(os.getcwd()+'/config.json', 'r', 'utf-8') as f:
        arrayw = json.loads(f.read())
        for c in arrayw:
            for key in c:
                arrayy.append(c[key])
    return {
        '__template__': 'manage.html',
        'manage': manage,
        'arrayy': arrayy,
    }

@get('/manage/create')
def create(request):
    return {
        '__template__': 'create.html',
        'create': create
    }

@get('/signin')
def signin(request):
    return {
        '__template__': 'signin.html',
        'signin': signin
    }

@post('/sign')
async def sign(request):
    data = await request.post()
    name = data['name']
    password = data['password']
    user = get_user()
    if not name:
        return None
    if not password:
        return None
    sha1 = hashlib.sha1()
    sha1.update(name.encode('utf-8'))
    sha1.update(b':')
    sha1.update(password.encode('utf-8'))
    if user['passwd'] != sha1.hexdigest():
        return None
    r = web.HTTPFound('/')
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user['passwd'] = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@post('/create_blog')
async def create_blog(request):
    data = await request.post()
    title = data['title']
    title2 = data['title2']
    content = data['content']
    image = data['image']
    print(title)

    uploadtime = time.time()
    localtime = time.strftime("%B %d %Y %H:%M:%S", time.localtime(uploadtime)) 
    image_filename = title2.replace(' ', '-') +'.'+ image.filename.split('.')[-1]
    image_filename = '/static/images/'+image_filename
    conf = {
        'localtime' : localtime,
        'image_filename':image_filename,
        'title':title,
        'title2':title2,
        'link':title2.replace(' ', '-'), }
    image_filename = os.getcwd()+image_filename
    md_filename = title2.replace(' ', '-') +'.md'
    with open(image_filename, 'wb') as f:
        f.write(data['image'].file.read())
    with codecs.open(os.getcwd()+'/templates/'+md_filename, 'w', 'utf-8') as f:
        f.write(u'%s'%(content))


    conf = {'%s'%title2.replace(' ', '-'):conf}

    with codecs.open(os.getcwd()+'/config.json', 'r', 'utf-8') as f:
        d = json.loads(f.read())
    with codecs.open(os.getcwd()+'/config.json', 'w', 'utf-8') as f:
        d.append(conf)
        j = json.dumps(d)
        f.write(j)


    r = web.HTTPFound('/manage')
    r.content_type = 'application/json'
    return r


@post('/manage/{title2}/delete')
async def delete_blog(title2):
    print(type(title2),title2)
    with codecs.open(os.getcwd()+'/config.json', 'r', 'utf-8') as f:
        d = json.loads(f.read())
        print(d)
    with codecs.open(os.getcwd()+'/config.json', 'w', 'utf-8') as f:
        c = 0
        for i in d:
            for key in i:
                if key == title2:
                    blog = i[title2]
                    d.remove(i)
                    j = json.dumps(d)
                    f.write(j)
    image_filename = blog['image_filename']
    md_filename = '/templates/'+title2 +'.md'
    try:
        os.remove(os.getcwd() + image_filename)
        os.remove(os.getcwd() + md_filename)
    except:
        print("remove err")

    r = web.HTTPFound('/manage')
    r.content_type = 'application/json'
    return r



