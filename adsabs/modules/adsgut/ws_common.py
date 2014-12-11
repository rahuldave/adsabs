from __future__ import with_statement

import sys, os, traceback

import mongogut
from mongogut.utilities import gettype
from mongogut import ptassets as itemsandtags
from mongogut.errors import doabort, MongoGutError

import flask
from flask import (Blueprint, request, url_for, Response, current_app as app, abort, render_template, jsonify)
from flask import  session, g, redirect, flash, escape, make_response
from flask.ext.mongoengine import MongoEngine
from flask.ext.login import current_user

import simplejson as json
import uuid
from random import choice



import datetime
from werkzeug import Response
from mongoengine import Document
from bson.objectid import ObjectId


from adsabs.extensions import mongoengine
from adsabs.extensions import solr

from config import config

adsgut_blueprint = Blueprint('adsgut', __name__,
                            template_folder="templates",
                            static_folder='static',
                            url_prefix='/adsgut',

)

adsgut_app=app
adsgut=adsgut_blueprint

POTENTIALUSERSTRING="""
<p>
The SAO/NASA Astrophysics Data System (ADS) is a Digital Library portal for researchers in Astronomy and
Physics, operated by the Smithsonian Astrophysical Observatory (SAO) under a NASA grant. The ADS maintains
three bibliographic databases containing more than 10.8 million records: Astronomy and Astrophysics, Physics,
and arXiv e-prints. The main body of data in the ADS consists of bibliographic records, which are searchable
through highly customizable query forms, and full-text scans of much of the astronomical literature which
can be browsed or searched via our full-text search interface at <a href="http://labs.adsabs.harvard.edu/adsabs/">http://labs.adsabs.harvard.edu/adsabs/</a>."
</p>
"""

POTENTIALUSERSTRING2="""
<p>
If you already have an account at ADS, you can go to <a href="http://labs.adsabs.harvard.edu/adsabs/user/">http://labs.adsabs.harvard.edu/adsabs/user/</a>, sign in, and click the %s link there to accept.
</p>
<p>
If you do not already have an ADS account, please <a href="http://labs.adsabs.harvard.edu/adsabs/user/signup">Sign up</a>! You will then be able to accept the invite from your account's Groups page.
</p>
"""

#tech to allow creating json from MomgoEngine Objects
def todfo(ci):
    cijson=ci.to_json()
    cidict=json.loads(cijson)
    return cidict

def todfl(cil):
    cijsonl=[e.to_json() for e in cil]
    cidictl=[json.loads(e) for e in cijsonl]
    return cidictl


class MongoEngineJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Document):
            return obj.to_mongo()
        elif isinstance(obj, ObjectId):
            return unicode(obj)
        elif isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        try:
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return json.JSONEncoder.default(self, obj)

def jsonify(*args, **kwargs):
    """ jsonify with support for MongoDB ObjectId
    """
    return Response(json.dumps(dict(*args, **kwargs), cls=MongoEngineJsonEncoder), mimetype='application/json')



#This next set of functions is used to obtain various quantities
#from http request GET and POST dictionaries in flask.

global _dictg
#FOR GET
def _dictg(k,d, listmode=False):
    val=d.get(k, [None])
    if d.has_key(k):
        d.pop(k)
    if listmode:
        return val
    else:
        return val[0]

global _dictp
#FOR POST
def _dictp(k,d, default=None):
    val=d.get(k, default)
    if d.has_key(k):
        d.pop(k)
    return val

global _opppostget
def _oppostget(postdict):
    op = _dictp('op', postdict)
    return op

global _opget
def _opget(qdict):
    op=_dictg('op', qdict)
    return op

global _userpostget
#gets a user from key useras in a POST request
def _userpostget(g, postdict):
    nick=_dictp('useras', postdict)
    if nick:
        useras=g.db._getUserForNick(g.currentuser, nick)
    else:
        useras=g.currentuser
    return useras

global _userget
#gets a user from key useras in a GET request
#userthere is used incase you want items just pertinent to the user
def _userget(g, qdict):
    nick=_dictg('useras', qdict)
    userthere=_dictg('userthere', qdict)
    if nick:
        useras=g.db._getUserForNick(g.currentuser, nick)
    else:
        useras=g.currentuser
    if userthere:
        usernick=useras.nick
    else:
        usernick=False
    return useras, usernick

#gets a sortspec. This looks like posting__whenposted:True
#which corresponds to and ascending sort. notee that i am currently
#exposing the inners of the database. it would be better to use a table
#to map this to user friendly names. TODO.
global _sortget
def _sortget(qdict):
    #a serialixed dict of ascending and field
    sortstring=_dictg('sort', qdict)
    if not sortstring:
        return {'field':'posting__whenposted', 'ascending':False}
    sort={}
    sort['field'], sort['ascending'] = sortstring.split(':')
    sort['ascending']=(sort['ascending']=='True')
    return sort

#sortspec from POST
global _sortpostget
def _sortpostget(qdict):
    #a serialixed dict of ascending and field
    sortstring=_dictp('sort', qdict)
    if not sortstring:
        return {'field':'posting__whenposted', 'ascending':False}
    sort={}
    sort['field'], sort['ascending'] = sortstring.split(':')
    sort['ascending']=(sort['ascending']=='True')
    return sort

#criteria is a multiple ampersand list, with colon separators.
#eg criteria=basic__fqin:eq:something&criteria=
#we create from it a criteria list of dicts
global _criteriaget
def _criteriaget(qdict):
    critlist=_dictg('criteria', qdict, True)
    if not critlist[0]:
        return False
    crit=[]
    for ele in critlist:
        cr={}
        cr['field'], cr['op'], cr['value'] = ele.split(':',2)
        crit.append(cr)
    return crit

#a serialised dict of arbitrary keys, with mongo style encoding
#operators are not represented here.(equality is assumed)
global _queryget
def _queryget(qdict):
    querylist=_dictg('query', qdict, True)
    if not querylist[0]:
        return {}
    q={}
    for ele in querylist:
        field, value = ele.split(':',1)
        if not q.has_key(field):
            q[field]=[]
        q[field].append(value)
    return q

#this is for pagination in the form pagetuplle=15:30
#the first is the item number to start from(offset), the second is the pagestyle.
global _pagetupleget
def _pagtupleget(qdict):
    pagtuplestring=_dictg('pagtuple', qdict)
    if not pagtuplestring:
        return None
    plist=pagtuplestring.split(':')
    pagtuple=[int(e) if e else -1 for e in pagtuplestring.split(':')]
    return pagtuple

#gets a list of items using their fqins
global _itemsget
def _itemsget(qdict):
    itemlist=_dictg('items', qdict, True)
    if not itemlist[0]:
        return []
    return itemlist

#like above, but uses post
global _itemspostget
def _itemspostget(qdict):
    itemlist=_dictp('items', qdict)
    if not itemlist:
        return []
    return itemlist

#gets bibcodes from POST
global _bibcodespostget
def _bibcodespostget(qdict):
    itemlist=_dictp('bibcode', qdict)
    if not itemlist:
        return []
    return itemlist

#gets a list of libraries (using their fqpns)
global _postablesget
def _postablesget(qdict):
    plist=_dictp('postables', qdict)
    if not plist:
        return []
    return plist

#get items and tags from the POST
#format is BLA
global _itemstagspostget
def _itemstagspostget(qdict):
    itemstagslist=_dictp('itemsandtags', qdict)
    if not itemstagslist:
        return []
    return itemstagslist


#get tag specs from the POST
#format is BLA
global _tagspecspostget
def _tagspecspostget(qdict):
    tagspecs=_dictp('tagspecs', qdict)
    if not tagspecs:
        return {}
    return tagspecs


#sets up the tag spec to tag an item
global _setupTagspec
def _setupTagspec(ti, useras):
    #atleast one of name or content must be there (tag or note)
    if not (ti.has_key('name') or ti.has_key('content')):
        doabort('BAD_REQ', "No name or content specified for tag")
    if not ti['tagtype']:
        doabort('BAD_REQ', "No tagtypes specified for tag")
    tagspec={}
    tagspec['creator']=useras.basic.fqin
    if ti.has_key('name'):
        tagspec['name'] = ti['name']
    if ti.has_key('tagmode'):
        tagspec['tagmode'] = ti['tagmode']
    if ti.has_key('content'):
        tagspec['content'] = ti['content']
    tagspec['tagtype'] = ti['tagtype']
    return tagspec

#a before_request is flask's place of letting you run code before
#the request is carried out. here is where we get info about the user
#from the database and all that

#current_user is obtained from the flask session
@adsgut.before_request
def before_request():
    try:
        #get the adsid which should be the email of the user
        adsid=current_user.get_username()
        #try getting the cookie id as well
        cookieid=current_user.get_id()
    except:
        #this fails if the user is not logged in. then set adsid to python None
        adsid=None
    #set up the database, and attach the database to the global g object.
    p=itemsandtags.Postdb(mongoengine)
    w=p.whosdb
    g.db=w
    g.dbp=p
    if not adsid:
        #if user not logged in, set user to the 'anonymouse' user
        adsid='anonymouse'
        user=g.db._getUserForAdsid(None, adsid)
    else:
        try:#look up the user based on their cookieid
            user=g.db._getUserForCookieid(None, cookieid)
            if user.adsid != adsid:#user changed their email
                user.adsid = adsid
                user.save(safe=True)
        except:
            #if we couldnt look up the user based on their cookieid
            #this situation can happen when a user is invited, has logged in
            #on classic or main, but is not in our adsgut system as yet
            adsgutuser=g.db._getUserForNick(None, 'adsgut')
            adsuser=g.db._getUserForNick(adsgutuser, 'ads')
            #we dont have the cookie, but we might have the adsid, because he was invited earlier
            try:#partially in our database
              user=g.db._getUserForAdsid(None, adsid)
              #take whatever cookieid the ads server allocated, and save it
              user.cookieid=cookieid
              user.save(safe=True)
            except:#not at all in our database
              #TODO: IF the next two dont happen transactionally we run into issues. Later we make this transactional
              #if the user was not invited, and not already there in adsgut database
              #this will happen the first time a user clicks libraries in the
              #profile page
              user=g.db.addUser(adsgutuser,{'adsid':adsid, 'cookieid':cookieid})
            #add the user to the flagship ads app, at the very least, to complete user
            #being in our database(addUser does not do this, bcoz the user
            #may partially exist in our database thanks to invitation)
            user, adspubapp = g.db.addUserToMembable(adsuser, 'ads/app:publications', user.nick)

    g.currentuser=user

#######################################################################################################################
#Information about users, groups, and apps
#######################################################################################################################



######################################################################

#create a group, app, or library, od type ptstr
def createMembable(g, request, ptstr):
    spec={}
    jsonpost=dict(request.json)
    #get user and name from POST json
    useras=_userpostget(g,jsonpost)
    name=_dictp('name', jsonpost)
    if not name:
        doabort("BAD_REQ", "No Name Specified")
    #get description from POST
    description=_dictp('description', jsonpost, '')
    spec['creator']=useras.basic.fqin
    spec['name']=name
    spec['description']=description
    postable=g.db.addMembable(g.currentuser, useras, ptstr, spec)
    return postable

def deleteMembable(g, request):
    jsonpost=dict(request.json)
    fqpn = _dictp('fqpn', jsonpost)
    useras = _userpostget(g, jsonpost)
    if fqpn is None:
        doabort("BAD_REQ", "No membable specified for  removal")
    g.dbp.removeMembable(g.currentuser, useras, fqpn)
    return 'OK'


#function to add a user to a library.
#TODO: do we want a useras here?
def addMemberToMembable(g, useras, member, fqpn, changerw):#fqmn/[changerw]
    user, membable=g.db.addMemberableToMembable(g.currentuser, useras, fqpn, member, changerw)
    return user, membable

def getMembersOfMembable(g, useras, fqpn):
    users=g.db.membersOfMembableFromFqin(g.currentuser,useras,fqpn)
    userdict={'users':users}
    return userdict

def getInvitedsForMembable(g, useras, fqpn):
    users=g.db.invitedsForMembableFromFqin(g.currentuser,useras,fqpn)
    userdict={'users':users}
    return userdict


#######################################################################################################################
#The next few return individual group and library profiles. The Info functions are web services used in the profile page
#######################################################################################################################
#TODO: BUG: to not leak info in profiles, cut short what the membable returned is, perhaps.
#mainly we do not want to leak info about other inviteds
#return information about the group or library. the world postable is a misnomer for now.
#this is a common function used in the web services below
def membable(g, useras, ownernick, name, ptstr):
    fqpn=ownernick+"/"+ptstr+":"+name
    membable, owner, creator=g.db.getMembableInfo(g.currentuser, useras, fqpn)
    isowner=False
    if g.db.isOwnerOfMembable(g.currentuser, useras, membable):
        isowner=True
    #get currentusers rw mode. Means nothing for groups and apps
    if pstr=="library":
        postablesin=g.currentuser.postablesin
        rw=False
        for p in postablesin:
            if p.fqpn==membable.basic.fqin:
                rw=p.readwrite
    else:
        rw=False
    return membable, isowner, rw, owner.presentable_name(), creator.presentable_name()



#making the import:
#TODO:make sure this gets into the config
#ADS_CLASSIC_LIBRARIES_URL = config.ADS_CLASSIC_LIBRARIES_URL
ADS_CLASSIC_LIBRARIES_URL = "http://adsabs.harvard.edu/cgi-bin/maint/export_privlib"
import requests

def perform_classic_library_query(parameters, headers, service_url):
    """
    function that performs a get request and returns a json object
    """
    #Perform the request
    r = requests.get(service_url, params=parameters, headers=headers)
    #Check for problems
    try:
        r.raise_for_status()
    except Exception, e:
        exc_info = sys.exc_info()
        app.logger.error("Author http request error: %s, %s\n%s" % (exc_info[0], exc_info[1], traceback.format_exc()))
        doabort("SRV_ERR", "Somewhing went wrong in contacting classic server")
    try:
        user_json = r.json()
    except Exception, e:
        exc_info = sys.exc_info()
        app.logger.error("Author JSON decode error: %s, %s\n%s" % (exc_info[0], exc_info[1], traceback.format_exc()))
        r = None
        user_json = {}
    return user_json

#make a query to bigquery to the title, author, etc
def perform_solr_bigquery(bibcodes):
    """
    function that performs a POST request and returns a json object
    """
    headers = {'Content-Type': 'big-query/csv'}
    url=config.SOLRQUERY_URL
    qdict = {
        'q':'text:*:*',
        'fq':'{!bitset compression=none}',
        'wt':'json',
        'fl':'bibcode,title,pubdate,author,alternate_bibcode'
    }
    #Perform the request
    qdict['rows']=len(bibcodes)
    rstr = "bibcode\n"+"\n".join(bibcodes)
    r = requests.post(url, params=qdict, data=rstr, headers=headers)
    #Check for problems
    try:
        r.raise_for_status()
    except Exception, e:
        exc_info = sys.exc_info()
        app.logger.error("Author http request error: %s, %s\n%s" % (exc_info[0], exc_info[1], traceback.format_exc()))

    try:
        d = r.json()
    except Exception, e:
        exc_info = sys.exc_info()
        app.logger.error("Author JSON decode error: %s, %s\n%s" % (exc_info[0], exc_info[1], traceback.format_exc()))
        r = None
        d = {}
    return d



#for a list of bibcodes, get bibquery results
@adsgut.route('/bigquery/bibcodes', methods=['POST'])
def get_bigquery_solr():
    if request.method=='POST':
        jsonpost=dict(request.json)
        bibcodes = _bibcodespostget(jsonpost)
        d=perform_solr_bigquery(bibcodes)
        return jsonify(d)


def removeMember(useras, fqpn, member):
    if fqpn is None or member is None:
        doabort("BAD_REQ", "Incomplete information supplied for member removal")
    g.db.removeMemberableFromMembable(g.currentuser, useras, fqpn, member)
    return jsonify({'status':'OK'})
####BACKWARD COMPAT ######

#remove a member(user/group) from a group/app/library. The user doing it could be the member
#or could be the owner of the membable
@adsgut.route('/memberremove', methods=['POST'])
def memberremove():#useras/member/gqpn
    if request.method=='POST':
        jsonpost=dict(request.json)
        fqpn = _dictp('fqpn', jsonpost)
        useras = _userpostget(g, jsonpost)
        member = _dictp('member', jsonpost)
        return removeMember(useras, fqpn, member)


#this will delete a group or a library. need owner user and fqpn of group/library.
@adsgut.route('/membableremove', methods=['POST'])
def membableremove():#useras/fqpn
    if request.method=='POST':
        status=deleteMembable(g, request)
        return jsonify({'status':status})

if __name__ == "__main__":
    adsgut.run(host="0.0.0.0", port=4000)
