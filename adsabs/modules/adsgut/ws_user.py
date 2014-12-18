from ws_common import *

#######################################################################################################################
#Information about users, groups, and apps
#######################################################################################################################



#this url gets information about a user
@adsgut.route('/user/<nick>')
def userInfo(nick):
    user=g.db.getUserInfo(g.currentuser, nick)
    #get additional info about user's libraries, including the reason
    #why the user is in the library
    postablesother, names = user.membableslibrary(pathinclude_p=True)
    #crikey stupid hack to have to do this bcoz of jsonify introspecting
    #mongoengine objects only
    jsons = [e.to_json() for e in postablesother]
    ds=[]
    for i, j in enumerate(jsons):
        d = json.loads(j)
        if names[d['fqpn']][0][2]==d['fqpn']:#direct membership overrides all else
            d['reason'] = ''
        else:
            reasons=[e[1] for e in names[d['fqpn']]]
            reasons=list(set(reasons))
            #eliminate all libraries (many!) the user is in because
            #os being part of the public group
            #(TODO: might be better done cleaner in membableslibrary)
            elim=[]
            for j,r in enumerate(reasons):
                if r=='group:public' and len(reasons) > 1:
                    elim.append(j)
            for j in elim:
                del reasons[j]
            #print "R2", reasons
            d['reason'] = ",".join(reasons)
        ds.append(d)
    #return information about the user and their libraries
    ujson = jsonify(user=user, postablelibs=ds)
    return ujson




#the libraries, apps and groups a user is directly in
#it should be called membablesuserisin but we are going with the historical url
@adsgut.route('/user/<nick>/postablesuserisin')
def postablesUserIsIn(nick):
    useras=g.db.getUserInfo(g.currentuser, nick)
    allpostables=g.db.membablesForUser(g.currentuser, useras)
    groups=[e['fqpn'] for e in allpostables if e['ptype']=='group']
    libraries=[e['fqpn'] for e in allpostables if e['ptype']=='library']
    apps=[e['fqpn'] for e in allpostables if e['ptype']=='app']
    groups.remove("adsgut/group:public")
    libraries.remove("adsgut/library:public")
    libraries.remove(useras.nick+"/library:default")
    return jsonify(groups=groups, libraries=libraries, apps=apps)

#this gets the libraries the user can access (write to is a not entirely
#accurate term because we do include read-only libraries here). the critical
#thing is that this includes libraires we are in due to membership in a group.
#this is used to poplate the dropdown menu, so unlike librariesuserisin and
#librariesusercanwriteto, this does not include libraries one can write to
#by dint of being in the public group
@adsgut.route('/user/<nick>/postablesusercanwriteto')
def postablesUserCanWriteTo(nick):
    useras=g.db.getUserInfo(g.currentuser, nick)
    allpostables=g.db.membablesUserCanWriteTo(g.currentuser, useras, public=False)
    #print "ALLPOSTABLES", [e.to_json() for e in allpostables]
    #groups=[e['fqpn'] for e in allpostables if e['ptype']=='group']
    libraries=[e['fqpn'] for e in allpostables if e['ptype']=='library']
    #apps=[e['fqpn'] for e in allpostables if e['ptype']=='app']
    #print "GLA", groups, libraries, apps
    #groups.remove("adsgut/group:public")
    if "adsgut/library:public" in libraries: libraries.remove("adsgut/library:public")
    if useras.nick+"/library:default" in libraries: libraries.remove(useras.nick+"/library:default")
    return jsonify(groups=[], libraries=libraries, apps=[])

#groups user is in, minus the public grouo
@adsgut.route('/user/<nick>/groupsuserisin')
def groupsUserIsIn(nick):
    useras=g.db.getUserInfo(g.currentuser, nick)
    groups=[e['fqpn'] for e in g.db.membablesForUser(g.currentuser, useras, "group")]
    groups.remove("adsgut/group:public")
    return jsonify(groups=groups)

# groups user owns
@adsgut.route('/user/<nick>/groupsuserowns')
def groupsUserOwns(nick):
    useras=g.db.getUserInfo(g.currentuser, nick)
    groups=[e['fqpn'] for e in g.db.ownerOfMembables(g.currentuser, useras, "group")]
    return jsonify(groups=groups)

# groups user is invited to
@adsgut.route('/user/<nick>/groupsuserisinvitedto')
def groupsUserIsInvitedTo(nick):
    useras=g.db.getUserInfo(g.currentuser, nick)
    groups=[e['fqpn'] for e in g.db.membableInvitesForUser(g.currentuser, useras, "group")]
    return jsonify(groups=groups)

# apps user is in
@adsgut.route('/user/<nick>/appsuserisin')
def appsUserIsIn(nick):
    useras=g.db.getUserInfo(g.currentuser, nick)
    apps=[e['fqpn'] for e in g.db.membablesForUser(g.currentuser, useras, "app")]
    return jsonify(apps=apps)


#apps user owns. not used yet
@adsgut.route('/user/<nick>/appsuserowns')
def appsUserOwns(nick):
    useras=g.db.getUserInfo(g.currentuser, nick)
    apps=[e['fqpn'] for e in g.db.ownerOfMembables(g.currentuser, useras, "app")]
    return jsonify(apps=apps)

#apps user is invited to: not used yet.
@adsgut.route('/user/<nick>/appsuserisinvitedto')
def appsUserIsInvitedTo(nick):
    useras=g.db.getUserInfo(g.currentuser, nick)
    apps=[e['fqpn'] for e in g.db.membableInvitesForUser(g.currentuser, useras, "app")]
    return jsonify(apps=apps)


#libraries user is in directly AND indirectly, read-only and readwrite.
#Includes those coming from public grp
@adsgut.route('/user/<nick>/librariesuserisin')
def librariesUserIsIn(nick):
    useras=g.db.getUserInfo(g.currentuser, nick)
    libs=[e['fqpn'] for e in g.db.membablesUserCanAccess(g.currentuser, useras, "library")]
    return jsonify(libraries=libs)

#all the libraries the user is in and which are writable.
#Includes those coming from public grp
@adsgut.route('/user/<nick>/librariesusercanwriteto')
def librariesUserCanWriteTo(nick):
    useras=g.db.getUserInfo(g.currentuser, nick)
    libs=[e['fqpn'] for e in g.db.membablesUserCanWriteTo(g.currentuser, useras, "library")]
    return jsonify(libraries=libs)

#the libraries a user owns
@adsgut.route('/user/<nick>/librariesuserowns')
def librariesUserOwns(nick):
    useras=g.db.getUserInfo(g.currentuser, nick)
    libs=[e['fqpn'] for e in g.db.ownerOfMembables(g.currentuser, useras, "library")]
    return jsonify(libraries=libs)

#libraries a user is invited to
@adsgut.route('/user/<nick>/librariesuserisinvitedto')
def librariesUserIsInvitedTo(nick):
    useras=g.db.getUserInfo(g.currentuser, nick)
    libs=[e['fqpn'] for e in g.db.membableInvitesForUser(g.currentuser, useras, "library")]
    return jsonify(libraries=libs)


################################################################################
#all the items saved in user's default library, currently not used
#no analog in new system for this
@adsgut.route('/user/<nick>/items')
def userItems(nick):
    useras=g.db.getUserInfo(g.currentuser, nick)
    num, vals=g.dbp.getItemsForQuery(g.currentuser, useras,
       {'library':[useras.nick+"/library:default"]} )
    #userdict={'count':num, 'items':[json.loads(v.to_json()) for v in vals]}
    return jsonify(count=num, items=vals)
#################################################################################

#The users simple tags, not singletonmode (ie no notes)
@adsgut.route('/user/<nick>/tagsuserowns')
def tagsUserOwns(nick):
    query=dict(request.args)
    useras, usernick= userget(g, query)
    tagtype= dictg('tagtype', query)
    stags=g.dbp.getTagsAsOwnerOnly(g.currentuser, useras, tagtype)
    stagdict={'simpletags':set([e.basic.name for e in stags[1]])}
    return jsonify(stagdict)

#these are the simple tags user owns as well as can write to by dint of being in a library
#or by being in a group which is a member of the tag. group membership of tags is not yet
#implemented, but the idea is for groups to come up with their own vocabulary systems
@adsgut.route('/user/<nick>/tagsusercanwriteto')
def tagsUserCanWriteTo(nick):
    query=dict(request.args)
    useras, usernick= userget(g, query)
    tagtype= dictg('tagtype', query)
    fqpn = dictg('fqpn',query)
    stags=g.dbp.getAllTagsForUser(g.currentuser, useras, tagtype, False, fqpn)
    stagdict={'simpletags':set([e.basic.name for e in stags[1]])}
    return jsonify(stagdict)

#this is only those tags obtained from membership in libs. Not currently used.
@adsgut.route('/user/<nick>/tagsasmember')
def tagsUserAsMember(nick):
    query=dict(request.args)
    useras, usernick= userget(g, query)
    tagtype= dictg('tagtype', query)
    fqpn = dictg('fqpn',query)
    stags=g.dbp.getTagsAsMemberOnly(g.currentuser, useras, tagtype, False, fqpn)
    stagdict={'simpletags':set([e.basic.name for e in stags[1]])}
    return jsonify(stagdict)

########################


dispatch_table_get = {
    'apps':{
        'isin':appsUserIsIn,
        'owns':appsUserOwns,
        'invitedto':appsUserIsInvitedTo
    },
    'groups':{
        'isin':groupsUserIsIn,
        'owns':groupsUserOwns,
        'invitedto':groupsUserIsInvitedTo
    },
    'libraries':{
        'isin':librariesUserIsIn,
        'owns':librariesUserOwns,
        'invitedto':librariesUserIsInvitedTo,
        'canwriteto':librariesUserCanWriteTo
    },
    'tags':{
        'owns': tagsUserOwns,
        'asmember': tagsUserAsMember,
        'canwriteto':tagsUserCanWriteTo
    }
}

table_of_ops = {}
for k in dispatch_table_get.keys():
    t="get_"+k+"_user_"
    k_table = dispatch_table_get[k]
    for k2 in k_table.keys():
        t2 = t + k2
        table_of_ops[t2]=k_table[k2]

@adsgut.route('/userN/<nick>')
def userEntryPoint(nick):
    if request.method=='GET':
        query=dict(request.args)
        op= opget(query)
        useras = userget(g, query)
        if op in table_of_ops.keys():
            f = table_of_ops[op]
            return f(nick)
        else:#any other op or no op
            return userInfo(nick)
    elif request.method=='POST':
        jsonpost=dict(request.json)
        op= oppostget('op')
        useras = userpostget(g, jsonpost)
        if op in table_of_ops.keys():
            f = table_of_ops[op]
            return f(nick)
        else:#any other op or no op
            return userInfo(nick)

