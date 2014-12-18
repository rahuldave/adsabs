from ws_common import *
#######################################################################################################################
#functions for creating groups and apps
#and for accepting invites.

#METHODS using POST have POST parameters on the right of the function
#######################################################################################################################


#create group/app/library. In our code we tend to use
#createMembable directly, rather than these endpoints.
#the useras is optional, vurrentuser is used otherwise



@adsgut.route('/group', methods=['POST'])#groupname/[description]/[useras]
def create_or_delete_Group():
    if request.method == 'POST':
        if op=="create_group" or op==None:
            newgroup=createMembable(g, request, "group")
            return jsonify(postable=newgroup)
        elif op=="delete_group":
            status=deleteMembable(g, request)
            return jsonify({'status':status})
        else:
            doabort("BAD_REQ", "Malformed Create or Delete Request")
    else:
        doabort("BAD_REQ", "GET not supported")

# @adsgut.route('/app', methods=['POST'])#name/[description]/[useras]
# def create_or_delete_App():
#     if request.method == 'POST':
#         if op=="create_app" or op==None:
#             newgroup=createMembable(g, request, "app")
#             return jsonify(postable=newgroup)
#         elif op=="delete_app":
#             status=deleteMembable(g, request)
#             return jsonify({'status':status})
#         else:
#             doabort("BAD_REQ", "Malformed Create or Delete Request")
#     else:
#         doabort("BAD_REQ", "GET not supported")


#TODO: if i am member of group, should I see inviteds, etc? Tamp the security down
@adsgut.route('/groupN/<groupowner>/group:<groupname>')
def groupEntryPoint(groupowner, groupname):
    if request.method=='GET':
        query=dict(request.args)
        op= opget(query)
        useras, _ = userget(g, query)
        grp, io, rw, on, cn = membable(g, useras, groupowner, groupname, "group")

        if op=="get_members":
            membersdict=getMembersOfMembable(g, useras, grp.basic.fqin)
            return jsonify(membersdict)
        elif op=="get_invitations":
            invitedsdict=getInvitedsForMembable(g, useras, grp.basic.fqin)
            return jsonify(invitedsdict)
        else:#any other op or no op
            return jsonify(group=grp, oname = on, cname = cn, io=io, rw=rw)
    elif request.method=='POST':
        jsonpost=dict(request.json)
        op= oppostget('op')
        useras = userpostget(g, jsonpost)
        grp, io, rw, on, cn = membable(g, useras, groupowner, groupname, "group")
        if op=="remove_member":
            member = dictp('member', jsonpost)
            return removeMember(useras, grp.basic.fqin, member)
        elif op=="accept_invitation":
            adsid= dictp('memberable', jsonpost)
            memberable=g.db._getUserForAdsid(g.currentuser, adsid)
            me, grp=g.db.acceptInviteToMembable(g.currentuser, grp.basic.fqin, memberable)
            return jsonify({'status':'OK', 'info': {'invited':me.nick, 'to': grp.basic.fqin, 'accepted':True}})
        elif op=="add_invitation":
            adsid= dictp('memberable', jsonpost)
            return inviteToGroup(useras, adsid, grp.basic.fqin)
        elif op=="change_description":
            description= dictp('description', jsonpost,'')
            me, grp = g.db.changeDescriptionOfMembable(g.currentuser, useras, grp.basic.fqin, description)
            return jsonify({'status': 'OK', 'info': {'user':useras.nick, 'for': grp.basic.fqin}})
        elif op=="change_ownership":
            adsid= dictp('memberable', jsonpost)
            memberable=g.db._getUserForAdsid(g.currentuser, adsid)
            newo, grp=g.db.changeOwnershipOfMembable(g.currentuser, useras, grp.basic.fqin, memberable)
            return jsonify({'status': 'OK', 'info': {'changedto':newo.nick, 'for': grp.basic.fqin}})
        elif op=="get_members":
            membersdict=getMembersOfMembable(g, useras, grp.basic.fqin)
            return jsonify(membersdict)
        elif op=="get_invitations":
            invitedsdict=getInvitedsForMembable(g, useras, grp.basic.fqin)
            return jsonify(invitedsdict)
        else:#send an empty POST
            return jsonify(group=grp, oname = on, cname = cn, io=io, rw=rw)

GRPINVSTRING="""
"%s has invited you to ADS Group %s. Go to your groups page to accept. 
You will be automatically enrolled in the library for that group.
"""
def inviteToGroup(useras, adsid, fqgn):
    gn=fqgn.split(':')[-1]
    changerw=False
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

    utba, p=g.db.inviteUserToMembable(g.currentuser, useras, fqgn, memberable, changerw)
    emailtitle="Invitation to ADS Group %s" % gn
    emailtext= GRPINVSTRING % (g.currentuser.adsid, gn)
    send_email_to_user(emailtitle, emailtext,[memberable.adsid])

    return jsonify({'status':'OK', 'info': {'invited':utba.nick, 'to':fqgn}})

@adsgut.route('/group/<po>/<pt>:<pn>/changes', methods=['POST'])#memberable/op/[description]
def doGroupChanges(po, pt, pn):
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
            return inviteToGroup(g.currentuser, memberable, fqpn)
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
        elif op=='description':
            description= dictp('description', jsonpost,'')
            mem, p = g.db.changeDescriptionOfMembable(g.currentuser, g.currentuser, fqpn, description)
            return jsonify({'status': 'OK', 'info': {'user':memberable, 'for': fqpn}})
        else:
            doabort("BAD_REQ", "No Op Specified")
    else:
        doabort("BAD_REQ", "GET not supported")




@adsgut.route('/group/<groupowner>/group:<groupname>/inviteds')
def groupInviteds(groupowner, groupname):
    fqgn=groupowner+"/group:"+groupname
    userdict=getInvitedsForMembable(g, request, fqgn)
    return jsonify(userdict)


#add user to group, or get members
@adsgut.route('/group/<groupowner>/group:<groupname>/members', methods=['GET', 'POST'])#fqmn/[changerw]
def addMembertoGroup_or_groupMembers(groupowner, groupname):
    #add permit to match user with groupowner
    fqgn=groupowner+"/group:"+groupname
    if request.method == 'POST':
        member, group=addMemberToPostable(g, request, fqgn)
        return jsonify({'status':'OK', 'info': {'member':member.basic.fqin, 'type':'group', 'postable':group.basic.fqin}})
    else:
        userdict=getMembersOfMembable(g, request, fqgn)
        return jsonify(userdict)

#add user to app, or get members
@adsgut.route('/app/<appowner>/app:<appname>/members', methods=['GET', 'POST'])#fqmn/[changerw]
def addMemberToApp_or_appMembers(appowner, appname):
    #add permit to match user with groupowner
    fqan=appowner+"/app:"+appname
    if request.method == 'POST':
        member, app=addMemberToPostable(g, request, fqan)
        return jsonify({'status':'OK', 'info': {'member':member.basic.fqin, 'type':'app', 'postable':app.basic.fqin}})
    else:
        userdict=getMembersOfMembable(g, request, fqan)
        return jsonify(userdict)






#get group info
@adsgut.route('/group/<groupowner>/group:<groupname>')
def groupInfo(groupowner, groupname):
    query=dict(request.args)
    useras, _ = userget(g, query)
    grp, io, rw, on, cn = membable(g, useras, groupowner, groupname, "group")
    return jsonify(group=grp, oname = on, cname = cn, io=io, rw=rw)

#get app info
@adsgut.route('/app/<appowner>/app:<appname>')
def appInfo(appowner, appname):
    query=dict(request.args)
    useras, _ = userget(g, query)
    a, io, rw, on, cn = membable(g, useras, appowner, appname, "app")
    return jsonify(app=a, oname = on, cname = cn, io=io, rw=rw)

