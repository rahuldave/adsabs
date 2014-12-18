from ws_common import *

#POST: create a new tag
#GET get tags for query
#currently unused. TODO: perhaps GET should be suppressed
#this is currently unused as we dont allow for free form creation of tags
#but this might be useful at some point in the future for vocabulary creation
@adsgut.route('/tags', methods=['POST', 'GET'])
def tags():
    if request.method=='POST':
        jsonpost=dict(request.json)
        useras = userpostget(g, jsonpost)
        tagspecs=tagspecspostget(jsonpost)
        newtags=[]
        for ti in tagspecs['tags']:
            if not ti.has_key('name'):
                doabort('BAD_REQ', "No name specified for tag")
            if not ti.has_key('tagtype'):
                doabort('BAD_REQ', "No tagtypes specified for tag")
            tagspec={}
            tagspec['creator']=useras.basic.fqin
            if ti.has_key('name'):
                tagspec['name'] = ti['name']
            tagspec['tagtype'] = ti['tagtype']
            t=g.dbp.makeTag(g.currentuser, useras, tagspec)
            newtags.append(t)

        tags={'status':'OK', 'info':{'item': i.basic.fqin, 'tags':[td for td in newtags]}}
        return jsonify(tags)
    else:
        query=dict(request.args)
        useras, usernick=userget(g, query)

        criteria= criteriaget(query)
        count, tags=g.dbp.getTagsForQuery(g.currentuser, useras,
            query, usernick, criteria)
        return jsonify({'tags':tags, 'count':count})


@adsgut.route('/itemsN/<ns>/<itemname>')
def itemEntryPoint(na, itemname):
    ifqin=ns+"/"+itemname
    if request.method=='GET':
        query=dict(request.args)
        op=opget(query)
        useras, _ = userget(g, query)
        if op=="get_tags":
            sort = sortget(query)
            fqpn = dictg('fqpn',query)
            taggingsdict, taggingsthispostable, taggingsdefault= g.dbp.getTaggingsConsistentWithUserAndItems(g.currentuser, useras, [ifqin], sort, fqpn)
            return jsonify(fqpn=fqpn, taggings=taggingsdict, taggingtp=taggingsthispostable, taggingsdefault=taggingsdefault)
        elif op=="get_libraries":
            sort = sortget(query)
            items = [ifqin]
            return get_postings(g, useras, items, sort)
        else:#any other op or no op
            sort = sortget(query)
            items = [ifqin]
            return get_postings(g, useras, items, sort)
    elif request.method=='POST':
        jsonpost=dict(request.json)
        op=oppostget('op')
        useras = userpostget(g, jsonpost)

        if op=="remove_tag":
            return tagsRemoveForItem(ns, itemname)
        elif op=="add_tags":
            itemtype=dictp('itemtype', jsonpost)
            itemspec={'name':itemname, 'itemtype':itemtype}
            #we use the fqpn to get the return to only get tags consistent with a certain library
            fqpn = dictp('fqpn',jsonpost)
            #get the tag specs
            tagspecs=tagspecspostget(jsonpost)
            return add_tags(g, useras, itemspec, tagspecs, fqpn)
        else:#send an empty POST
            doabort('BAD_REQ', "No op given")
#GET tags for an item
#or POST: tag an item

def add_tags(g, useras, itemspec, tagspecs, fqpn):
    i=g.dbp.saveItem(g.currentuser, useras, itemspec)
    #get the tag specs
    newtaggings=[]
    if not tagspecs.has_key(i.basic.name):
        doabort('BAD_REQ', "No itemname specified to tag")
    for ti in tagspecs[i.basic.name]:
        tagspec=setupTagspec(ti, useras)
        i,t,it,td=g.dbp.tagItem(g.currentuser, useras, i, tagspec)
        newtaggings.append(td)
    #get ALL the taggings consistent with this item and this user back
    taggingsdict, taggingsthispostable, taggingsdefault= g.dbp.getTaggingsConsistentWithUserAndItems(g.currentuser, useras, [i.basic.fqin], None, fqpn)
    return jsonify(fqpn=fqpn, taggings=taggingsdict, taggingtp=taggingsthispostable, taggingsdefault=taggingsdefault)

@adsgut.route('/tags/<ns>/<itemname>', methods=['GET', 'POST'])
def tagsForItem(ns, itemname):
    ifqin=ns+"/"+itemname
    if request.method == 'POST':
        jsonpost=dict(request.json)
        useras = userpostget(g, jsonpost)
        itemtype=dictp('itemtype', jsonpost)
        itemspec={'name':itemname, 'itemtype':itemtype}
        #we use the fqpn to get the return to only get tags consistent with a certain library
        fqpn = dictp('fqpn',jsonpost)
        #get the tag specs
        tagspecs=tagspecspostget(jsonpost)
        return add_tags(g, useras, itemspec, tagspecs, fqpn)
    else:
        query=dict(request.args)
        useras, usernick=userget(g, query)

        sort = sortget(query)
        fqpn = dictg('fqpn',query)
        taggingsdict, taggingsthispostable, taggingsdefault= g.dbp.getTaggingsConsistentWithUserAndItems(g.currentuser, useras, [ifqin], sort, fqpn)
        return jsonify(fqpn=fqpn, taggings=taggingsdict, taggingtp=taggingsthispostable, taggingsdefault=taggingsdefault)

#remove a tag from an item, for a particular library.
@adsgut.route('/tagsremove/<ns>/<itemname>', methods=['POST'])
def tagsRemoveForItem(ns, itemname):
    ifqin=ns+"/"+itemname
    if request.method == 'POST':
        jsonpost=dict(request.json)
        useras = userpostget(g, jsonpost)
        tagname=dictp('tagname', jsonpost)
        tagtype=dictp('tagtype', jsonpost)
        fqpn = dictp('fqpn',jsonpost)
        fqtn = dictp('fqtn',jsonpost)
        #will use useras for the namespace if it is removing your own stuff
        #for a library owner removing a tag 'viagra' the full fqtn is needed
        if fqtn==None:#nothing was sent over the wire
            fqtn = useras.nick+'/'+tagtype+":"+tagname

        if fqpn==None:#nuke it, this happens for saved items (for private notes too)
          val=g.dbp.untagItem(g.currentuser, useras, fqtn, ifqin)
        else:#remove tag from postable (should only affect pinpostables)
          val=g.dbp.removeTaggingFromPostable(g.currentuser, useras, fqpn, ifqin, fqtn)
        taggingsdict, taggingsthispostable, taggingsdefault= g.dbp.getTaggingsConsistentWithUserAndItems(g.currentuser, useras, [ifqin], None, fqpn)
        return jsonify(fqpn=fqpn, taggings=taggingsdict, taggingtp=taggingsthispostable, taggingsdefault=taggingsdefault)



@adsgut.route('/itemsN')
def itemsEntryPoint():
    if request.method=='GET':
        query=dict(request.args)
        op=opget(query)
        useras, _ = userget(g, query)
        if op=="get_taggings":
            sort = sortget(query)
            items = itemsget(query)
            return get_taggings(g, useras, items, sort)
        elif op=="get_libraries":
            sort = sortget(query)
            items = itemsget(query)
            return get_postings(g, useras, items, sort)
        elif op=="get_libraries_and_taggings":
            itemsTaggingsAndPostings()
        else:#any other op or no op
            sort = sortget(query)
            items = itemsget(query)
            return get_postings(g, useras, items, sort)
    elif request.method=='POST':
        jsonpost=dict(request.json)
        op=oppostget('op')
        useras = userpostget(g, jsonpost)

        if op=="add_libraries":
            items = itemspostget(jsonpost)
            fqpo = postablesget(jsonpost)
            itemtype=dictp('itemtype', jsonpost)
            return add_postings(g, useras, items, fqpo, itemtype)
        elif op=="add_taggings":
            items = itemspostget(jsonpost)
            tagspecs=tagspecspostget(jsonpost)
            itemtype=dictp('itemtype', jsonpost)
            return add_taggings(g, useras, items, tagspecs, itemtype)
        elif op=="get_libraries_and_taggings":
            itemsTaggingsAndPostings()
        else:#send an empty POST
            doabort('BAD_REQ', "No op given")
#GET is used to get the taggings consistent with user for a set of items (unused currently)
#POST used in postform to tag items without worrying about library (will go in default library)
#notice no fqpn here, since we dont care for the library
#this function is used in the postform interface

def get_taggings(g, useras, items, sort):
    taggingsdict,_,junk=g.dbp.getTaggingsConsistentWithUserAndItems(g.currentuser, useras,
            items, sort)
    return jsonify(taggings=taggingsdict)

def add_taggings(g, useras, items, tagspecs, itemtype):
    newtaggings=[]
    for name in items:
        itemspec={'name':name, 'itemtype':itemtype}
        i=g.dbp.saveItem(g.currentuser, useras, itemspec)
        if not tagspecs.has_key(name):
            doabort('BAD_REQ', "No itemname specified to tag")
        for ti in tagspecs[name]:
            tagspec=setupTagspec(ti, useras)
            i,t,it,td=g.dbp.tagItem(g.currentuser, useras, i, tagspec)
            newtaggings.append(td)
    taggingsdict,_,junk=g.dbp.getTaggingsConsistentWithUserAndItems(g.currentuser, useras,
            items, None)
    return jsonify(taggings=taggingsdict)

@adsgut.route('/items/taggings', methods=['POST', 'GET'])#items/itemtype/tagspecs/user
def itemsTaggings():
    if request.method=='POST':
        jsonpost=dict(request.json)
        useras = userpostget(g, jsonpost)
        items = itemspostget(jsonpost)
        tagspecs=tagspecspostget(jsonpost)
        itemtype=dictp('itemtype', jsonpost)
        return add_taggings(g, useras, items, tagspecs, itemtype)
    else:
        query=dict(request.args)
        useras, usernick=userget(g, query)
        sort = sortget(query)
        items = itemsget(query)
        return get_taggings(g, useras, items, sort)

#POST: usedin postform to post items into a postable
#GET: just get the consistent postings
def get_postings(g, useras, items, sort):
    postingsdict=g.dbp.getPostingsConsistentWithUserAndItems(g.currentuser, useras,
            items, sort)
    return jsonify(postings=postingsdict)

def add_postings(g, useras, items, fqpo, itemtype):
    pds=[]
    for name in items:
        itemspec={'name':name, 'itemtype':itemtype}
        i=g.dbp.saveItem(g.currentuser, useras, itemspec)
        for fqpn in fqpo:
            i,pd=g.dbp.postItemIntoPostable(g.currentuser, useras, fqpn, i)
            pds.append(pd)
    #return consistent postings for the user
    postingsdict=g.dbp.getPostingsConsistentWithUserAndItems(g.currentuser, useras,
        items, None)
    return jsonify(postings=postingsdict)

@adsgut.route('/items/postings', methods=['POST', 'GET'])
def itemsPostings():
    if request.method=='POST':
        jsonpost=dict(request.json)
        useras = userpostget(g, jsonpost)
        items = itemspostget(jsonpost)
        fqpo = postablesget(jsonpost)
        itemtype=dictp('itemtype', jsonpost)
        return add_postings(g, useras, items, fqpo, itemtype)
    else:
        query=dict(request.args)
        useras, usernick=userget(g, query)
        sort = sortget(query)
        items = itemsget(query)
        return get_postings(g, useras, items, sort)

#both POST and GET are used to get taggings and postings for a set of items
#this is as we might not want to put all items in a GET querystring
#this is the one used in the filter interface
#currently used for all items
#to make faster we must put in pagination
@adsgut.route('/items/taggingsandpostings', methods=['POST', 'GET'])#user/fqpn/items
def itemsTaggingsAndPostings():
    if request.method=='POST':
        #"THIS WILL NOT BE TO POST STUFF IN BUT TO GET RESULTS"
        jsonpost=dict(request.json)
        useras = userpostget(g, jsonpost)
        sort = sortpostget(jsonpost)
        items = itemspostget(jsonpost)
        fqpn = dictp('fqpn',jsonpost)
        postingsdict=g.dbp.getPostingsConsistentWithUserAndItems(g.currentuser, useras, items, sort)
        taggingsdict, taggingsthispostable, taggingsdefault=g.dbp.getTaggingsConsistentWithUserAndItems(g.currentuser, useras, items, sort, fqpn)
        return jsonify(fqpn=fqpn, postings=postingsdict, taggings=taggingsdict, taggingtp=taggingsthispostable, taggingsdefault=taggingsdefault)
    else:
        query=dict(request.args)
        useras, usernick=userget(g, query)
        sort = sortget(query)
        items = itemsget(query)
        fqpn = dictg('fqpn',query)
        postingsdict=g.dbp.getPostingsConsistentWithUserAndItems(g.currentuser, useras,
            items, sort)
        taggingsdict, taggingsthispostable, taggingsdefault=g.dbp.getTaggingsConsistentWithUserAndItems(g.currentuser, useras,
            items, sort, fqpn)
        return jsonify(fqpn=fqpn, postings=postingsdict, taggings=taggingsdict, taggingtp=taggingsthispostable, taggingsdefault=taggingsdefault)


#add or get an itemtype. currently not used, we do this in python code
@adsgut.route('/itemtypes', methods=['POST', 'GET'])
def itemtypes():
    if request.method=='POST':
        jsonpost=dict(request.json)
        useras = userpostget(g, jsonpost)
        itspec={}
        itspec['creator']=useras.basic.fqin
        itspec['name'] = dictp('name', jsonpost)
        if not itspec['name']:
            doabort("BAD_REQ", "No name specified for itemtype")
        itspec['postable'] = dictp('postable', jsonpost)
        if not itspec['postable']:
            doabort("BAD_REQ", "No postable specified for itemtype")
        newitemtype=g.dbp.addItemType(g.currentuser, useras, itspec)
        return jsonify({'status':'OK', 'info':newitemtype})
    else:
        query=dict(request.args)
        useras, usernick=userget(g, query)
        criteria= criteriaget(query)
        isitemtype=True
        count, thetypes=g.dbp.getTypesForQuery(g.currentuser, useras, criteria, usernick, isitemtype)
        return jsonify({'types':thetypes, 'count':count})

#add or get an tagtype. currently not used, we do this in python code
@adsgut.route('/tagtypes', methods=['POST', 'GET'])
def tagtypes():
    ##useras?/name/itemtype
    #q={useras?, userthere?, sort?, pagetuple?, criteria?, stags|tagnames ?, postables?}
    if request.method=='POST':
        jsonpost=dict(request.json)
        useras = userpostget(g, jsonpost)
        itspec={}
        itspec['creator']=useras.basic.fqin
        itspec['name'] = dictp('name', jsonpost)
        itspec['tagmode'] = dictp('tagmode', jsonpost)
        itspec['singletonmode'] = dictp('singletonmode',jsonpost)
        if not itspec['tagmode']:
            del itspec['tagmode']
        else:
            itspec['tagmode']=bool(itspec['tagmode'])
        if not itspec['singletonmode']:
            del itspec['singletonmode']
        else:
            itspec['singletonmode']=bool(itspec['singletonmode'])
        if not itspec['name']:
            doabort("BAD_REQ", "No name specified for itemtype")
        itspec['postable'] = dictp('postable', jsonpost)
        if not itspec['postable']:
            doabort("BAD_REQ", "No postable specified for itemtype")
        newtagtype=g.dbp.addTagType(g.currentuser, useras, itspec)
        return jsonify({'status':'OK', 'info':newtagtype})
    else:
        query=dict(request.args)
        useras, usernick=userget(g, query)
        criteria= criteriaget(query)
        isitemtype=False
        count, thetypes=g.dbp.getTypesForQuery(g.currentuser, useras, criteria, usernick, isitemtype)
        return jsonify({'types':thetypes, 'count':count})

#this is just a function to split up an itemstring. used in postform
#TODO: should be replaced by an internal function:this is kind of stupid
#(again both GET and POST)
@adsgut.route('/itemsinfo', methods = ['POST', 'GET'])
def itemsinfo():
    if request.method=='POST':
        jsonpost=dict(request.json)
        itemstring=jsonpost.get('items',[''])
        items=itemstring.split(':')
        #print "LLLL", itemstring, items
        theitems=[{'basic':{'name':i.split('/')[-1], 'fqin':i}} for i in items]
    else:
        query=dict(request.args)
        itemstring=query.get('items',[''])[0]
        items=itemstring.split(':')
        theitems=[{'basic':{'name':i.split('/')[-1], 'fqin':i}} for i in items]
    return jsonify({'items': theitems, 'count':len(theitems)})

