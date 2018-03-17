#-*- coding: utf-8 -*-
# Local Agent 4 Plex
import re
import difflib
from urllib2 import HTTPError
# URLs
DB__BASE_URL = Prefs['txt_DatabaseUrl']
HD_POSTER = Prefs['chk_HDPoster']
HD_POSTER_PROXY = Prefs['txt_HDPosterProxy']
SEARCH_ACT = 'act=search'

REQUEST_DELAY = 0



def Start():
    # Nothing to do, just pass
    pass

class LA4PAgent(Agent.Movies):
    name = 'Local Agent 4 Plex'
    languages = ['ja','zh','en']
    primary_provider = True
    accepts_from = ['com.plexapp.agents.localmedia']
    contribute_to = ['com.plexapp.agents.arzon']
    #prev_search_provider = 0

    def search(self, results, media, lang, manual):
        Log('***************Search start****************')
        Log('Media title: %s', media.title)
        code = self.getCode(media.name)
        Log('Code: %s',code)
        found = self.doSearch(code,None)
        index = 0
        for i in found:    
            score = self.doScore(code, i['id'], index)
            if score < 50:
                score = self.doScore(code,i['title'], index)
                pass
            Log('Score = %s',score)
            msr = MetadataSearchResult(id=i['id'],thumb=i['thumb'],name=i['title'],score=score,lang='ja')
            results.Append(msr)
            Log('%s results appended:', len(results))
            index += 1
            pass
        if len(results) == 1 and results[0].score > 60:
            results[0].score = 100
        Log('Media title: %s', media.title)
        Log('***************Search end****************')
        
    
    def doSearch(self, keyword, option = None):
        found = []
        try:
            Log('We are ready to go to: ' + DB__BASE_URL + keyword + '?' + SEARCH_ACT)
            data = JSON.ObjectFromURL(DB__BASE_URL + keyword + '?' + SEARCH_ACT, sleep = REQUEST_DELAY)
            Log('key word: %s',keyword)
            cnt = 0;
            for i in data:
                Log(i)
                url = i['Url']
                title = i['Title'].decode('utf-8')
                id = i['MovieId']
                found.append({'url':url, 'thumb':'', 'title':title, 'id':id})
                Log('***************Meta Found****************')
                to = found[cnt]
                cnt += 1
                Log('Url: %s, Thumb: %s, Title: %s, id: %s',to['url'],to['thumb'],to['title'],to['id'])
                pass
        except HTTPError:
                pass
        return found

    def doScore(self, code, id, index):
        score = 0
        numerator = 0
        Log('Code: %s, ID: %s',code, id)
        for i in difflib.SequenceMatcher(None,code.upper(),id.upper()).get_matching_blocks():
            numerator += i[2]
            pass
        score = 100 * numerator / max(len(code),len(id)) * pow(0.8, index)
        return score

    def getCode(self, mediaName):
        text = mediaName.replace(' ','_')
        result = text;
        p = r'\w+[_-]\d+'
        so = re.search(p,text)
        if so is not None:
            result = so.group()
        #else:
        #    so = re.search(r'\d+_\d+',text)
        #    if so is not None:
        #        result = so.group()
        #        pass
        #    pass
        return result

    def update(self, metadata, media, lang, force = False):
        Log('***************Update start****************')
        Log('Metadata.id:                %s', metadata.id)
        # Get the metadata object
        result = self.doUpdate(metadata.id)[0]

        # Year
        metadata.year = int((result['date']).split('-')[0])

        # Origninally available date
        metadata.originally_available_at=Datetime.ParseDate(str(result['date']))

        # Original title
        metadata.original_title = metadata.id

        # Directors
        metadata.directors.clear()
        for d in result['director']:
            director = metadata.directors.new()
            director.name = d
            pass
        #Log('Line 136: Director: %s',metadata.directors.name)

        # Studio
        metadata.studio = result['studio']

        # Collection
        metadata.collections.clear()
        metadata.collections.add(result['collection'])

        # Tagline
        metadata.tagline = metadata.id

        # Genres
        metadata.genres.clear()
        if len(result['genre']) > 0:
            for g in result['genre']:
                metadata.genres.add(g)
                pass
            pass
        # Roles
        if len(result['role']) > 0:
            metadata.roles.clear()
            i = 0
            for r in result['role']:
                role = metadata.roles.new()
                try:
                    role.name = r
                except:
                    role.actor = r
                    pass
                role.photo=result['avatar'][i]
                i += 1
                pass
            pass
        i = 1

        # Poster
        if (HD_POSTER and len(HD_POSTER_PROXY) > 0):
            try:
                poster_url = result['poster']
                metadata.posters[poster_url] = Proxy.Media(self.getHDPoster(poster_url),sort_order = i)
                i += 1
            except:
                pass 
            finally:
                i = 1
                pass
            pass

        # Art
        if len(result['art']) > 0:
            for a in result['art']:
                try:
                    metadata.art[a] = Proxy.Preview(HTTP.Request(a),sort_order = i)
                    i += 1
                except:
                    Log('****************Can\'t get, GFW GG ***************')
                    pass
                pass
            # Add full cover as backdrop for manually HD poster or uncencored backdrop
            metadata.art[poster_url] = Proxy.Media(HTTP.Request(poster_url),sort_order = i) 
        Log('Media title: %s', media.title)                    
        Log('****************all done***************')

    def doUpdate(self, id):
        found = []
        url = DB__BASE_URL + id
        Log('Request:                          %s',url)
        data = JSON.ObjectFromURL(url, sleep = REQUEST_DELAY)[0]
        poster=data['Poster']
                
        date = data['Date']
        if date.strip()=='0000-00-00':
            date='2008-01-01'
            pass
        try:
            director = []
            if len(data['Directors']) > 0:
                director = data['Directors']
        except:
            pass
        studio = data['Studio']
        try:
            collection = []
            if len(data['Collections']) > 0:
                collection = data['Collections'][0]
        except:
            collection = ''
        
        genre = data['Genres']
       
        try:
            role = []
            avatar = []
            for r in data['Roles']: #can be multiple
                role.append(r)
                pass
            for a in data['Avatars']:
                avatar.append(a)
        except:
            pass
        art = []
        try:
            for i in data['Art']:
                art.append(i)
        except:
            pass
        found.append({'date':date, 'director':director,'studio':studio,
                      'collection':collection,'genre':genre,'role':role,'avatar':avatar,'poster':poster,'art':art})
        Log('found poster:        %s', poster)
        return found

    def getHDPoster(self, url):
        Log.Info('******************************')
        Log.Info('Request for HD Poster:                 %s',url)
        poster = HTTP.Request(HD_POSTER_PROXY,values={'url':url})
       
        
        return poster.content
