from ws_common import *

@adsgut.route('/library', methods=['POST'])#name/[description]/[useras]
def createLibrary():
    if request.method == 'POST':
        newlibrary=createMembable(g, request, "library")
        return jsonify(postable=newlibrary)
    else:
        doabort("BAD_REQ", "GET not supported")

@adsgut.route('/library', methods=['POST'])#libraryname/[description]/[useras]
def create_or_delete_Library():
    if request.method == 'POST':
        if op=="create_library" or op==None:
            newgroup=createMembable(g, request, "library")
            return jsonify(postable=newgroup)
        elif op=="delete_library":
            status=deleteMembable(g, request)
            return jsonify({'status':status})
        else:
            doabort("BAD_REQ", "Malformed Create or Delete Request")
    else:
        doabort("BAD_REQ", "GET not supported")

@adsgut.route('/libraryN/<libraryowner>/library:<libraryname>')
def libraryEntryPoint(libraryowner, libraryname):
    if request.method=='GET':
        query=dict(request.args)
        op= opget(query)
        useras, usernick = userget(g, query)
        lib, io, rw, on, cn = membable(g, useras, libraryowner, libraryname, "library")
        if op=="get_members":
            membersdict=getMembersOfMembable(g, useras, lib.basic.fqin)
            return jsonify(membersdict)
        elif op=="get_invitations":
            invitedsdict=getInvitedsForMembable(g, useras, lib.basic.fqin)
            return jsonify(invitedsdict)
        elif op=='get_tags':
            criteria= criteriaget(query)
            q= queryget(query)
            return get_tags(g, useras, usernick, lib.basic.fqin, q, criteria)
        elif op=='get_items':
            format = dictg('format', query)
            sort = sortget(query)
            pagtuple = pagtupleget(query)
            criteria= criteriaget(query)
            q= queryget(query)
            return get_items(g, useras, usernick, lib.basic.fqin, format, q, criteria, pagtuple, sort)
        else:#any other op or no op
            return jsonify(library=lib, oname = on, cname = cn, io=io, rw=rw)
    elif request.method=='POST':
        jsonpost=dict(request.json)
        op= oppostget('op')
        useras = userpostget(g, jsonpost)
        lib, io, rw, on, cn = membable(g, useras, libraryowner, libraryname, "library")
        if op=="remove_items":
            items = itemspostget(jsonpost)
            return remove_items(g, useras, items, lib.basic.fqin)
        elif op=="add_items":
            itemtype= dictp('itemtype', jsonpost)
            items = itemspostget(jsonpost)
            return add_items(g, useras, items, lib.basic.fqin)
        elif op=="save_items":
            items = itemspostget(jsonpost)
            itemtype = dictp('itemtype', jsonpost)
            return save_items(g, useras, items, itemtype)
        elif op=="remove_member":
            member = dictp('member', jsonpost)
            return removeMember(useras, lib.basic.fqin, member)
        elif op=="add_member":
            member= dictp('member', jsonpost)
            changerw= dictp('changerw', jsonpost)
            if not changerw:
                changerw=False
            return addMember(useras, lib.basic.fqin, member)
        elif op=="accept_invitation":
            adsid= dictp('memberable', jsonpost)
            memberable=g.db._getUserForAdsid(g.currentuser, adsid)
            me, lib=g.db.acceptInviteToMembable(g.currentuser, lib.basic.fqin, memberable)
            return jsonify({'status':'OK', 'info': {'invited':me.nick, 'to': grp.basic.fqin, 'accepted':True}})
        elif op=="add_invitation":
            changerw= dictp('changerw', jsonpost)
            if changerw==None:
                changerw=False
            adsid= dictp('memberable', jsonpost)
            return inviteToLibrary(useras, adsid, lib.basic.fqin, changerw)
        elif op=="change_description":
            description= dictp('description', jsonpost,'')
            me, lib = g.db.changeDescriptionOfMembable(g.currentuser, useras, lib.basic.fqin, description)
            return jsonify({'status': 'OK', 'info': {'user':useras.nick, 'for': lib.basic.fqin}})
        elif op=="change_permissions":#could even be a group, for user also want fqin
            #change to take nick
            memberable= dictp('memberable', jsonpost)
            mtype=gettype(memberable)
            memberable=g.db._getMemberableForFqin(g.currentuser, mtype, memberable)
            memberable, lib = g.db.toggleRWForMembership(g.currentuser, useras, lib.basic.fqin, memberable)
            return jsonify({'status': 'OK', 'info': {'memberable':memberable.basic.fqin, 'for': lib.basic.fqin}})
        elif op=="change_ownership":
            adsid= dictp('memberable', jsonpost)
            memberable=g.db._getUserForAdsid(g.currentuser, adsid)
            newo, lib=g.db.changeOwnershipOfMembable(g.currentuser, useras, lib.basic.fqin, memberable)
            return jsonify({'status': 'OK', 'info': {'changedto':newo.nick, 'for': lib.basic.fqin}})
        elif op=="get_members":
            membersdict=getMembersOfMembable(g, useras, lib.basic.fqin)
            return jsonify(membersdict)
        elif op=="get_invitations":
            invitedsdict=getInvitedsForMembable(g, useras, lib.basic.fqin)
            return jsonify(invitedsdict)
        else:#send an empty POST
            return jsonify(library=lib, oname = on, cname = cn, io=io, rw=rw)

LIBINVSTRING="""
"%s has invited you to ADS Library %s. Go to your libraries page to accept. 
"""
def inviteToLibrary(useras, adsid, fqln, changerw=False):
    ln=fqln.split(':')[-1]
    try:
        memberable=g.db._getUserForAdsid(g.currentuser, adsid)
    except:
        #there in Giovanni system
        adsuser = AdsUser.from_email(adsid)
        if adsuser==None:
            doabort("BAD_REQ", "No such User")
        cookieid = adsuser.get_id()
        adsid = adsuser.get_username()
        adsgutuser=g.db._getUserForNick(None, 'adsgut')
        adsuser=g.db._getUserForNick(adsgutuser, 'ads')
        memberable=g.db.addUser(adsgutuser,{'adsid':adsid, 'cookieid':cookieid})
        #per usual add to publications
        memberable, adspubapp = g.db.addUserToMembable(adsuser, 'ads/app:publications', memberable.nick)

    utba, p=g.db.inviteUserToMembable(g.currentuser, useras, fqln, memberable, changerw)
    emailtitle="Invitation to ADS Library %s" % ln
    emailtext= LIBINVSTRING % (g.currentuser.adsid, ln)
    send_email_to_user(emailtitle, emailtext,[memberable.adsid])

    return jsonify({'status':'OK', 'info': {'invited':utba.nick, 'to':fqln}})

@adsgut.route('/postable/<po>/<pt>:<pn>/changes', methods=['POST'])#memberable/op/[description]
def doPostableChanges(po, pt, pn):
    #add permit to match user with groupowner
    fqpn=po+"/"+pt+":"+pn
    if request.method == 'POST':
        jsonpost=dict(request.json)
        memberable= dictp('memberable', jsonpost)
        changerw= dictp('changerw', jsonpost)
        if changerw==None:
            changerw=False
        #for inviting this is adsid(email) of user invited.
        #for accepting this is your own email(adsid)
        if not memberable:
            doabort("BAD_REQ", "No User Specified")
        op= dictp('op', jsonpost)
        if not op:
            doabort("BAD_REQ", "No Op Specified")
        if op=="invite":
            try:
                memberable=g.db._getUserForAdsid(g.currentuser, memberable)
            except:
                adsuser = AdsUser.from_email(memberable)
                if adsuser==None:
                    doabort("BAD_REQ", "No such User")
                cookieid = adsuser.get_id()
                adsid = adsuser.get_username()
                adsgutuser=g.db._getUserForNick(None, 'adsgut')
                adsuser=g.db._getUserForNick(adsgutuser, 'ads')
                memberable=g.db.addUser(adsgutuser,{'adsid':adsid, 'cookieid':cookieid})
                #per usual add to publications
                memberable, adspubapp = g.db.addUserToMembable(adsuser, 'ads/app:publications', memberable.nick)

            utba, p=g.db.inviteUserToMembable(g.currentuser, g.currentuser, fqpn, memberable, changerw)
            emailtitle="Invitation to ADS Library %s" % pn
            emailtext="%s has invited you to ADS Library %s. Go to your libraries page to accept." % (g.currentuser.adsid, pn)
            send_email_to_user(emailtitle, emailtext,[memberable.adsid])

            return jsonify({'status':'OK', 'info': {'invited':utba.nick, 'to':fqpn}})
        elif op=='accept':
            memberable=g.db._getUserForAdsid(g.currentuser, memberable)
            me, p=g.db.acceptInviteToMembable(g.currentuser, fqpn, memberable)
            return jsonify({'status':'OK', 'info': {'invited':me.nick, 'to': fqpn, 'accepted':True}})
        elif op=='decline':
            memberable=g.db._getUserForAdsid(g.currentuser, memberable)
            #TODO: not implemented yet add something to invitations to mark declines.
            return jsonify({'status': 'OK', 'info': {'invited':memberable, 'to': fqpn, 'accepted':False}})
        elif op=='changeowner':
            #you must be the current owner
            memberable=g.db._getUserForAdsid(g.currentuser, memberable)
            newo, p=g.db.changeOwnershipOfMembable(g.currentuser, g.currentuser, fqpn, memberable)
            return jsonify({'status': 'OK', 'info': {'changedto':memberable, 'for': fqpn}})
        elif op=='togglerw':
            #here memberable could be a user or a group (whose membership to library you are toggling)
            #in either case here we need the fqin
            mtype=gettype(memberable)
            memberable=g.db._getMemberableForFqin(g.currentuser, mtype, memberable)
            mem, p = g.db.toggleRWForMembership(g.currentuser, g.currentuser, fqpn, memberable)
            return jsonify({'status': 'OK', 'info': {'user':memberable, 'for': fqpn}})
        elif op=='description':
            description= dictp('description', jsonpost,'')
            mem, p = g.db.changeDescriptionOfMembable(g.currentuser, g.currentuser, fqpn, description)
            return jsonify({'status': 'OK', 'info': {'user':memberable, 'for': fqpn}})
        else:
            doabort("BAD_REQ", "No Op Specified")
    else:
        doabort("BAD_REQ", "GET not supported")






@adsgut.route('/library/<libraryowner>/library:<libraryname>/inviteds')
def libraryInviteds(libraryowner, libraryname):
    fqln=libraryowner+"/library:"+libraryname
    userdict=getInvitedsForMembable(g, request, fqln)
    return jsonify(userdict)


#add user or group to library, (but we use next one actually). we do use this for members
@adsgut.route('/library/<libraryowner>/library:<libraryname>/members', methods=['GET', 'POST'])#fqmn/[changerw]
def addMemberToLibrary_or_libraryMembers(libraryowner, libraryname):
    #add permit to match user with groupowner
    fqln=libraryowner+"/library:"+libraryname
    if request.method == 'POST':
        member, library=addMemberToPostable(g, request, fqln)
        return jsonify({'status':'OK', 'info': {'member':member.basic.fqin, 'type':'library', 'postable':library.basic.fqin}})
    else:
        userdict=getMembersOfMembable(g, request, fqln)
        return jsonify(userdict)


#add memberable to postable(library)
#Only currently used to add a group toa library, but could be used to add users. But we
#always invite users. Bulk can use a script anyways.
@adsgut.route('/postable/<po>/<pt>:<pn>/members', methods=['GET', 'POST'])#fqmn/[changerw]
def addMemberToPostable_or_postableMembers(po, pt, pn):
    fqpn=po+"/"+pt+":"+pn
    if request.method == 'POST':
        member, postable=addMemberToPostable(g, request, fqpn)
        dictis = {'status':'OK', 'info': {'member':member.basic.fqin, 'type':pt, 'postable':postable.basic.fqin}}
        return jsonify(dictis)
    else:
        userdict=getMembersOfMembable(g, request, fqpn)
        return jsonify(userdict)


#get library info
@adsgut.route('/library/<libraryowner>/library:<libraryname>')
def libraryInfo(libraryowner, libraryname):
    query=dict(request.args)
    useras, _ = userget(g, query)
    l, io, rw, on, cn = membable(g, useras, libraryowner, libraryname, "library")
    return jsonify(library=l, oname=on, cname=cn, io=io, rw=rw)



#POST posts items into postable, GET gets items for postable consistent with user.
#all items in post must be of same type
#this is the workhorse function for the library items page
#the tags areimplicitly obtained through the posting document

def add_items(g, useras, items, fqpn):
    pds=[]
    for name in items:
            itemspec={'name':name, 'itemtype':itemtype}
            i=g.dbp.saveItem(g.currentuser, useras, itemspec)
            i,pd=g.dbp.postItemIntoPostable(g.currentuser, useras, fqpn, i)
            pds.append(pd)
    #if this works send the posting documents back. note this will include
    #others posts in pd.hist but they are all in this library so there is no leakage
    itempostings={'status':'OK', 'postings':pds, 'postable':fqpn}
    return jsonify(itempostings)

def get_items(g, useras, usernick, fqpn, format, q, criteria, pagtuple, sort):
    if not q.has_key('postables'):
            q['postables']=[]
    q['postables'].append(fqpn)
    #print "Q is", q, query, useras, usernick
    #By this time query is popped down
    if format=='json':
        count, items=g.dbp.getItemsForQueryWithTags(g.currentuser, useras,
            q, usernick, criteria, sort, pagtuple)
    elif format=='csv':
        count, items=g.dbp.getItemsForQueryWithTags(g.currentuser, useras,
            q, usernick, criteria, sort, pagtuple)
        csvstring="#count="+str(count)+",postable="+fqpn+"\n"
        for i in items:
            s=i['basic']['name']
            for t in i['tags']:
                l=s+","+t
                csvstring=csvstring+l+"\n"
            if len(i['tags'])==0:
                csvstring=csvstring+s+",\n"
        return Response(csvstring, mimetype='text/csv')
    else:
        count, items=g.dbp.getItemsForQuery(g.currentuser, useras,
            q, usernick, criteria, sort, pagtuple)
    return jsonify({'items':items, 'count':count, 'postable':fqpn})

@adsgut.route('/postable/<po>/<pt>:<pn>/items', methods=['GET', 'POST'])#user/items/itemtype
def itemsForPostable(po, pt, pn):
    if request.method=='POST':
        jsonpost=dict(request.json)
        useras = userpostget(g, jsonpost)
        #get a list of 'names'(bibcodes) for the itemtype (pubs)
        items = itemspostget(jsonpost)
        #also get the itemtypr
        itemtype= dictp('itemtype', jsonpost)
        fqpn=po+"/"+pt+":"+pn
        return add_items(g, useras, items, fqpn)
    else:
        query=dict(request.args)
        useras, usernick= userget(g, query)
        #get user, sort, and pagetuple. with user, also get if u only want that user's posts
        #otheerwise the useras is used to make sure the user has the righ permissions
        sort = sortget(query)
        pagtuple = pagtupleget(query)
        #criteria is used for further filtering (currently not used)
        criteria= criteriaget(query)
        postable= po+"/"+pt+":"+pn
        q= queryget(query)
        #Add the postable wanted to the query. The query q is used to get
        #tagtypes and tagnames if wanted
        return get_items(g, useras, usernick, fqpn, None, q, criteria, pagtuple, sort)
        

#same as above but only GET and is used to get json
#the one difference is that we get the tags along the way explicitly
@adsgut.route('/postable/<po>/<pt>:<pn>/json', methods=['GET'])
def jsonItemsForPostable(po, pt, pn):
    query=dict(request.args)
    useras, usernick= userget(g, query)

    sort = sortget(query)
    pagtuple = pagtupleget(query)
    criteria= criteriaget(query)
    postable= po+"/"+pt+":"+pn
    q= queryget(query)
    return get_items(g, useras, usernick, fqpn, 'json', q, criteria, pagtuple, sort)


#same as above but for csv
@adsgut.route('/postable/<po>/<pt>:<pn>/csv', methods=['GET'])
def csvItemsForPostable(po, pt, pn):
    query=dict(request.args)
    useras, usernick= userget(g, query)
    sort = sortget(query)
    pagtuple = pagtupleget(query)
    #pagtuple=(2,1)
    criteria= criteriaget(query)
    postable= po+"/"+pt+":"+pn
    q= queryget(query)
    return get_items(g, useras, usernick, fqpn, 'csv', q, criteria, pagtuple, sort)



#just specialized to library
@adsgut.route('/library/<libraryowner>/library:<libraryname>/items')
def libraryItems(libraryowner, libraryname):
    return itemsForPostable(libraryowner, "library", libraryname)


#the POST is used to post an item-tag pair into a postable
#the GET gets the taggings for a query in a postable
#TODO: more docs needed. Do not believe this is currently used

@adsgut.route('/postable/<po>/<pt>:<pn>/taggings', methods=['GET', 'POST'])
def taggingsForPostable(po, pt, pn):
    if request.method=='POST':
        jsonpost=dict(request.json)
        useras = userpostget(g, jsonpost)
        itemsandtags = itemstagspostget(jsonpost)
        fqpn=po+"/"+pt+":"+pn
        tds=[]
        for d in itemsandtags:
            fqin=d['fqin']
            fqtn=d['fgtn']
            td=g.dbp.getTaggingDoc(g.currentuser, useras, fqin, fqtn)
            i,t,td=g.dbp.postTaggingIntoPostable(g.currentuser, useras, fqpn, td)
            tds.append(td)
        itemtaggings={'status':'OK', 'taggings':tds, 'postable':fqpn}
        return jsonify(itemtaggings)
    else:
        query=dict(request.args)
        useras, usernick= userget(g, query)

        #need to pop the other things like pagetuples etc. Helper funcs needed
        sort = sortget(query)
        criteria= criteriaget(query)
        postable= po+"/"+pt+":"+pn
        q= queryget(query)
        if not q.has_key('postables'):
            q['postables']=[]
        q['postables'].append(postable)
        #By this time query is popped down
        count, taggings=g.dbp.getTaggingsForQuery(g.currentuser, useras,
            q, usernick, criteria, sort)
        return jsonify({'taggings':taggings, 'count':count, 'postable':postable})

#GET all tags consistent with user for a particular postable and further query
#this is a workhorse function which populates the lhs set of tags

def get_tags(g, useras, usernick, fqpn, q, criteria):
    pt, pn=fqpn.split('/')[-1].split(':')
    if not q.has_key('postables'):
        q['postables']=[]
    #BUG: this seems identical. Whats wrong?
    if pt=='library' and pn=='default':#in saved items get from all postables(libraries) we are in
        #i believe this is currently done in the downstream function
        q['postables'].append(fqpn)
    else:
        q['postables'].append(fqpn)

    count, tags=g.dbp.getTagsForQueryFromPostingDocs(g.currentuser, useras,
        q, usernick, criteria)
    return jsonify({'tags':tags, 'count':count})

@adsgut.route('/postable/<po>/<pt>:<pn>/tags', methods=['GET'])
def tagsForPostable(po, pt, pn):
    query=dict(request.args)
    useras, usernick= userget(g, query)
    #criteria currently unused
    criteria= criteriaget(query)
    postable= po+"/"+pt+":"+pn
    #tagnames and tagtypes used in query to get only those tags compatible with the tag used
    #this is used for filtering in the user interface
    q= queryget(query)
    return get_tags(g, useras, usernick, fqpn, q, criteria)
    


#remove items from library

def remove_items(g, useras, items, fqpn):
    if fqpn is None:
            doabort("BAD_REQ", "No postable specified for item removal")
    for itemfqin in items:
        g.dbp.removeItemFromPostable(g.currentuser, useras, fqpn, itemfqin)
    return jsonify({'status':'OK', 'info':items})

@adsgut.route('/itemsremove', methods=['POST'])#fqpn/itemsto remove/user
def itemsremove():
    if request.method=='POST':
        jsonpost=dict(request.json)
        fqpn = dictp('fqpn', jsonpost)
        useras = userpostget(g, jsonpost)
        items = itemspostget(jsonpost)
        return remove_items(g, useras, items, fqpn)
        

#POST saveItems(s), this is used in the posting form under 'export'
#GET could take a bunch of items as arguments, or a query
#I dont believe GET is used. TODO: we should perhaps suppress the GET

def save_items(g, useras, items, itemstype):
    creator=useras.basic.fqin
    if not itemtype:
            doabort("BAD_REQ", "No itemtype specified for item")
    for name in items:
        itspec={'creator':creator, 'name':name, 'itemtype':itemtype}
        newitem=g.dbp.saveItem(g.currentuser, useras, itspec)
    return jsonify({'status':'OK', 'info':items})

@adsgut.route('/items', methods=['POST', 'GET'])
def items():
    ##useras?/name/itemtype
    #q={useras?, userthere?, sort?, pagetuple?, criteria?, stags|tagnames ?, postables?}
    if request.method=='POST':
        jsonpost=dict(request.json)
        useras = userpostget(g, jsonpost)
        items = itemspostget(jsonpost)
        itemtype = dictp('itemtype', jsonpost)
        return save_items(g, useras, items, itemtype)
    else:
        query=dict(request.args)
        useras, usernick= userget(g, query)
        #query stuff
        sort = sortget(query)
        pagtuple = pagtupleget(query)
        criteria= criteriaget(query)
        #By this time query is popped down
        count, items=g.dbp.getItemsForQuery(g.currentuser, useras,
            query, usernick, criteria, sort, pagtuple)
        return jsonify({'items':items, 'count':count})

