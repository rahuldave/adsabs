from ws_common import *
from flask.ext.mongoengine.wtf import model_form
from flask_debugtoolbar import DebugToolbarExtension
from flask.ext.wtf import Form, RecaptchaField
from wtforms import TextField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email

class InviteForm(Form):
    memberable = TextField('username', validators=[DataRequired(), Email()])
    op = HiddenField(default="invite")
    changerw = BooleanField("Can Post?")
    recaptcha = RecaptchaField()

class InviteFormGroup(Form):
    memberable = TextField('username', validators=[DataRequired(), Email()])
    op = HiddenField(default="invite")
    recaptcha = RecaptchaField()
@adsgut.route('/user/<nick>/profile/html')
def userProfileHtml(nick):
    user=g.db.getUserInfo(g.currentuser, nick)
    return render_template('userprofile.html', theuser=user, useras=g.currentuser)

@adsgut.route('/email/<adsid>/profile/html')
def userProfileFromAdsidHtml(adsid):
    user=g.db.getUserInfoFromAdsid(g.currentuser, adsid)
    return render_template('userprofile.html', theuser=user, useras=g.currentuser)

#Thes next two creates a profile for the groups the user has.
#see https://dl.dropboxusercontent.com/u/75194/usergroupprofile.png
@adsgut.route('/user/<nick>/profilegroups/html')
def userProfileGroupsHtml(nick):
    user=g.db.getUserInfo(g.currentuser, nick)
    return render_template('userprofilegroups.html', theuser=user, useras=g.currentuser)

@adsgut.route('/email/<adsid>/profilegroups/html')
def userProfileGroupsFromAdsidHtml(adsid):
    user=g.db.getUserInfoFromAdsid(g.currentuser, adsid)
    return render_template('userprofilegroups.html', theuser=user, useras=g.currentuser)

from adsabs.modules.user.user import AdsUser
from adsabs.modules.user.user import send_email_to_user

#creating an invitation to a group or library (or app: not implemented yet, TODO)
#this is a very different endpoint, only used from the per library or per group
#web pages to make invitations. it is NOT part of the API.
@adsgut.route('/postable/<po>/<pt>:<pn>/makeinvitations', methods=['POST'])
def makeInvitations(po, pt, pn):
    fqpn=po+"/"+pt+":"+pn
    if request.method == 'POST':
        if pt=="library":
            form = InviteForm()
        else:
            form = InviteFormGroup()
        if form.validate():
            #email of user being invited
            memberable=form.memberable.data
            changerw=False
            #for libraries, whether the read-write checkbox was checked
            if pt=="library":
              changerw=form.changerw.data
            if not memberable:
                 doabort("BAD_REQ", "No User Specified")
            #print "memberable", memberable, changerw
            potentialuserstring=""
            try:
                user=g.db._getUserForAdsid(g.currentuser, memberable)
            except:
                adsuser = AdsUser.from_email(memberable)
                #get the system users so that we can create a partial user
                adsgutuser=g.db._getUserForNick(None, 'adsgut')
                adsappuser=g.db._getUserForNick(adsgutuser, 'ads')
                if adsuser==None:#not in giovanni db, just add to ours
                    #add a potential user with 'NOCOOKIEYET'to our db
                    potentialuser=g.db.addUser(adsgutuser,{'adsid':memberable, 'cookieid':'NOCOOKIEYET-'+str(uuid.uuid4())})
                    user=potentialuser
                    potentialuserstring=POTENTIALUSERSTRING
                else:#already in giovanni db, add to ours
                    cookieid = adsuser.get_id()#get from giovanni db
                    adsid = adsuser.get_username()
                    user=g.db.addUser(adsgutuser,{'adsid':adsid, 'cookieid':cookieid})
                    #sice already there add to publications.
                    user, adspubapp = g.db.addUserToMembable(adsappuser, 'ads/app:publications', user.nick)
                    potentialuserstring=""
            potentialuserstring2=POTENTIALUSERSTRING2
            #ok got user, now invite by adding invitation into the database
            utba, p=g.db.inviteUserToMembable(g.currentuser, g.currentuser, fqpn, user, changerw)
            #queue up an invitation email
            emailtitle="Invitation to ADS Library %s" % pn
            ptmap={'group':'Group (and associated library)', 'library':"Library"}
            ptmap2={'group':'My Groups', 'library':"Libraries"}
            emailtext="%s has invited you to ADS %s %s." % (g.currentuser.adsid, ptmap[pt], pn)
            emailtext = emailtext+potentialuserstring+potentialuserstring2%ptmap2[pt]
            send_email_to_user(emailtitle, emailtext,[user.adsid])
            passdict={}
            passdict[pt+'owner']=po
            passdict[pt+'name']=pn
            flash("Invite sent", 'success')
            #redirect to user or group profile
            return redirect(url_for("adsgut."+pt+"ProfileHtml", **passdict))
        else:
            junk=1
        return profileHtmlNotRouted(po, pn, pt, inviteform=form)


#get group profile
@adsgut.route('/postable/<groupowner>/group:<groupname>/profile/html')
def groupProfileHtml(groupowner, groupname):
    return profileHtmlNotRouted(groupowner, groupname, "group", inviteform=None)


#get app profile, not used currently
@adsgut.route('/postable/<appowner>/app:<appname>/profile/html')
def appProfileHtml(appowner, appname):
    return profileHtmlNotRouted(appowner, appname, "app", inviteform=None)


#get library profile
@adsgut.route('/postable/<libraryowner>/library:<libraryname>/profile/html')
def libraryProfileHtml(libraryowner, libraryname):
    return profileHtmlNotRouted(libraryowner, libraryname, "library", inviteform=None)

#general function used above which gets the right flask-wtf form for recaptcha for invitations
def profileHtmlNotRouted(powner, pname, ptype, inviteform=None):
    p, owner, rw, on, cn=membable(g, g.currentuser, powner, pname, ptype)
    if not inviteform:
      if ptype=="library":
        inviteform = InviteForm()
      else:
        inviteform = InviteFormGroup()
    #print p.to_json()
    return render_template(ptype+'profile.html', thepostable=p, thepostablejson=p.to_json(), owner=owner, rw=rw, inviteform=inviteform, useras=g.currentuser, po=powner, pt=ptype, pn=pname)


#this is the workhorse for displaying items, for any library
@adsgut.route('/postable/<po>/<pt>:<pn>/filter/html')
def postableFilterHtml(po, pt, pn):
    querystring=request.query_string
    p, owner, rw, on, cn=membable(g, g.currentuser, po, pn, pt)
    pflavor='pos'
    if pn=='public' and po=='adsgut' and pt=='library':
        pflavor='pub'
    if pn=='default' and pt=='library':
        tqtype='stags'
        pflavor='udg'#even though this is now a library, we still call it udg in js code
    else:
        pflavor=p.basic.fqin
        tqtype='tagname'
    tqtype='tagname'
    return render_template('postablefilter.html', thepostablejson=p.to_json(), p=p, po=po, pt=pt, pn=pn, pflavor=pflavor, querystring=querystring, tqtype=tqtype, useras=g.currentuser, owner=owner, rw=rw)

#get the user defaukt library's items
@adsgut.route('/postable/<nick>/library:default/filter/html')
def udlHtml(nick):
    return postableFilterHtml(nick, "library", "default")

#get the user default library from email
@adsgut.route('/postablefromadsid/<adsid>/library:default/filter/html')
def udlHtmlFromAdsid(adsid):
    user=g.db.getUserInfoFromAdsid(g.currentuser, adsid)
    return postableFilterHtml(user.nick, "library", "default")

#get the public library. The public group's library is not displayed at this moment
@adsgut.route('/postable/adsgut/library:public/filter/html')
def publicHtml():
    return postableFilterHtml("adsgut", "library", "public")

#A POST to set up the postform in html. It works from the export menu
#gets the bibcodes, uses a bigquery solr request to populate the titles
@adsgut.route('/postform/<itemtypens>/<itemtypename>/html', methods=['POST'])
def postForm(itemtypens, itemtypename):
    qstring=""
    itemtype=itemtypens+"/"+itemtypename
    if request.method=='POST':
        if itemtype=="ads/pub":
            current_page=request.referrer
            if request.values.has_key('numRecs'):
                numrecs = request.values.get('numRecs')
            else:
                numrecs = config.SEARCH_DEFAULT_ROWS
            if request.values.has_key('bibcode'):
                bibcodes = request.values.getlist('bibcode')
            else:
                try:
                    query_components = json.loads(request.values.get('current_search_parameters'))
                except:
                    return render_template('errors/generic_error.html', error_message='Error. Please try later.')

                #update the query parameters to return only what is necessary
                query_components.update({
                    'facets': [],
                    'fields': ['bibcode'],
                    'highlights': [],
                    'rows': str(numrecs)
                    })

                list_type = request.values.get('list_type')
                if 'sort' not in query_components:
                    from adsabs.core.solr.query_builder import create_sort_param
                    query_components['sort'] = create_sort_param(list_type=list_type)

                req = solr.create_request(**query_components)
                if 'bigquery' in request.values:
                    from adsabs.core.solr import bigquery
                    bigquery.prepare_bigquery_request(req, request.values['bigquery'])
                req = solr.set_defaults(req)
                resp = solr.get_response(req)
                #return error if solr messes up
                if resp.is_error():
                    return render_template('errors/generic_error.html', error_message='Error while loading bibcodes for posting. Please try later.')

                bibcodes = [x.bibcode for x in resp.get_docset_objects()]
            items=["ads/"+i for i in bibcodes]
        elif itemtype=="ads/search":#not implemented yet
            itemstring=query.get('items',[''])[0]

        theitems=[]
        if itemtype=="ads/pub":
            theitems=[{ 'basic':{'name':i.split('/')[-1],'fqin':i}} for i in items]
        elif itemtype=="ads/search":#not implemented yet
            theitems=[{ 'basic':{'name':itemstring,'fqin':'ads/'+itemstring}}]
        #if only one item we allow notes as yet
        singlemode=False
        if len(theitems) ==1:
            singlemode=True
        nameable=False
        if itemtype=="ads/pub":
            qstring=":".join(items)
        elif itemtype=="ads/search":
            nameable=True
            qstring=itemstring
        if nameable and singlemode:
            nameable=True

        return render_template('postform_fancy.html', items=theitems,
            querystring=qstring,
            singlemode=singlemode,
            nameable=nameable,
            itemtype=itemtypename,
            curpage=current_page,
            useras=g.currentuser)


#Use GET to get the classic libraries. TODO: make this POST as its destructive
#on our database BUG This is used with the import/reimport classic button. The idea
#will be to do it as post AJAX, with the database (user.classicimported) changed by a queue process once we have the
#queue in place. This way the user can come back. This is a long running process.

#TODO: separate from chrome as we actually populate libraries in here. Or have that happen via
#a POST web service.
@adsgut.route('/classic/<cookieid>/libraries', methods=['GET'])
def get_classic_libraries(cookieid, password=None):

    headers = {'User-Agent':'ADS Script Request Agent'}
    parameters = {'cookie':cookieid}
    try:
        libjson=perform_classic_library_query(parameters, headers, ADS_CLASSIC_LIBRARIES_URL)
    except:
        #import sys
        #print ">>>", sys.exc_info()
        doabort("SRV_ERR", "Somewhing went wrong in contacting classic server")
    useras=g.db._getUserForCookieid(g.currentuser, cookieid)
    useras.classicimported=True
    useras.save(safe=True)
    ret=g.dbp.populateLibraries(g.currentuser, useras, libjson)
    if ret:
        return redirect(url_for('adsgut.userProfileHtml', nick=useras.nick))
    else:
        return redirect('/')
