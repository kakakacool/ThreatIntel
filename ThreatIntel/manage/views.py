from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, StreamingHttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext, loader
import django.utils.html as html
from django.utils.translation import ugettext
from manage.models import *

import sys
#sys.path = sys.path + ['', '/usr/lib/python2.7', '/usr/lib/python2.7/plat-linux2', '/usr/lib/python2.7/lib-tk', '/usr/lib/python2.7/lib-old', '/usr/lib/python2.7/lib-dynload', '/usr/local/lib/python2.7/dist-packages', '/usr/lib/python2.7/dist-packages', '/usr/lib/python2.7/dist-packages/PIL', '/usr/lib/python2.7/dist-packages/gst-0.10', '/usr/lib/python2.7/dist-packages/gtk-2.0', '/usr/lib/pymodules/python2.7', '/usr/lib/python2.7/dist-packages/ubuntu-sso-client', '/usr/lib/python2.7/dist-packages/ubuntuone-client', '/usr/lib/python2.7/dist-packages/ubuntuone-control-panel', '/usr/lib/python2.7/dist-packages/ubuntuone-couch', '/usr/lib/python2.7/dist-packages/ubuntuone-installer', '/usr/lib/python2.7/dist-packages/ubuntuone-storage-protocol'] 
from data import *


# the decorator prevents access and redirects users who have not logged in
@login_required(redirect_field_name='/login')
def query(request):
    '''Takes user's query and processes it'''    
    if request.method == 'POST':
        return query_execute(request)
    form = QueryForm()
    return render_to_response('query.html', {'form': form, 'state': ""}, RequestContext(request))

def construct_providers(config):
    # Construct providers from user's info
    providers = []
    providers.append(DShieldDataProvider())
    providers.append(ShadowServerDataProvider())
    ptankkey = config.ptankkey
    if len(ptankkey) == 0:
        ptankkey = None
    providers.append(PhishTankDataProvider(apikey=ptankkey))
    vtotkey = config.vtotkey
    if len(vtotkey) != 0:
        providers.append(VirusTotalDataProvider(apikey=vtotkey))
    titancert = config.titancert
    titankey = config.titankey
    if len(titancert) != 0 and len(titankey) != 0:
        providers.append(TitanDataProvider(titancert, titankey))
    return providers

def query_execute(request):
    form = QueryForm(request.POST)
    if not form.is_valid():
        pass # do some error thing
    query = form.cleaned_data["query"].strip()
    ctx = RequestContext(request, {"form": form, "state": ""})
    providers = construct_providers(request.user.config)
    data = DataProvider.queryn(query, providers)
    def produce():
        tqheader = loader.get_template("query.html")
        tqentry = loader.get_template("query_entry.html")
        tqfooter = loader.get_template("query_footer.html")
        yield tqheader.render(ctx)
        ctx.push()
        for entry in data:
            ctx["entry"] = entry
            yield tqentry.render(ctx)
            yield ' ' * 1024
        ctx.pop()
        yield tqfooter.render(ctx)
    return StreamingHttpResponse(produce())

# the decorator prevents access and redirects users who have not logged in
@login_required(redirect_field_name='/login')
def get_keys(request):
    '''Processes and displays keys API keys entered by user'''
    state = 'Please enter your API keys'
    # if user submitted the form
    try:
        inst = request.user.config
    except UserConfiguration.DoesNotExist:
        inst = None
    if request.method == 'POST':
        form = KeysForm(request.POST, instance=inst)
        if form.is_valid():
            form.save()
            state = 'Your keys have been saved!'
    else:
        form = KeysForm(instance=inst)
    return render_to_response('apikeys.html', {'form': form, 'state': state}, RequestContext(request))
