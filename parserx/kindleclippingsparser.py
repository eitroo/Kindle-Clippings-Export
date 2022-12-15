#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import codecs

class KindleClippingsParser():

    class ParseError(Exception):
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return repr(self.value)
    
    def __init__(self, f):
        self.fp = f

    def parse(self):
        notes = [str(n.strip()) for n in (self.fp.read().split("\n=========="))]            

        return (self.parse_note(note) for note in notes
                if note != '')

    def parse_note(self, note):

        def collect_title(n, i):
            title = str()
            iterm = n[i:].split('\n')[0].rfind('(')
            for index, c in enumerate(n[i:]):
                if c == ' ':
                    # if the next character's an '(', we've found our terminator.
                    if index + 1 == iterm:
                        #print "got end of title."
                        return (title, index + 2 + i)
                if note[index + 1] == '\n':
                    #raise self.ParseError("caught unexpected newline when looking for title (at %d). Got title '%s'" % (i, title))
                    return (title, index + 1 + i)
                else:

                    title += c

        def collect_author(n, i):
            author = str()
            for index, c in enumerate(n[i:]):
                if c == ')':
                    # we've got our terminator!
                    #print "got end of author."
                    return (author, index + 1 + i)
                elif note[index + 1] == '\n':
#                    print "Caught unexpected newline when looking for author. Assuming unknown or omitted." 
                    return ("Unknown", i-1)
                else:
                    author += c


        def collect_note_highlight(n, i):
            if n[i] == '\n' and n[i+1] == '-' and n[i+2] == ' ':
                i += 3
                note = str()
                for index, c in enumerate(n[i:]):
                    if c == ' ':
                        #print "got end of note-highlight."
                        return (note, index + 1 + i)
                    else:
                        # here should follow a "-" and Note|Highlight
                        if n[i:][:4] == 'Note':
                            #print "it's a note"
                            return ("Note", index + 4 + i)
                        elif n[i:][:9] == 'Highlight':
                            #print "it's a highlight"
                            return ("Highlight", index + 9 + i)
                        elif n[i:][:8] == 'Bookmark':
                            return ("Bookmark", index + 8 + i)
                        else:
                            #print title + '\n' + author + '\n'
                            raise self.ParseError("parse error: expected Note, Highlight or Bookmark at %d" % i)

            else:
                raise self.ParseError("parse error at %d. Expected '\r\n- ', got '%s'." % (i, n[i:][:3]))
                exit

        def collect_location(n, i):
            loc = str()
            if n[i:][:4] == ' on ':
                i += 4
                for index, c in enumerate(n[i:]):
                    if c == '|':
                        #print "got end-of-location"
                        loc = loc.strip() + ','
                        i += 1 + index
                        break
                    else:
                        loc += c
                        
            if n[i:][:6] == " Loc. ":
                i += 6
                for index, c in enumerate(n[i:]):
                    if c == '|':
                        #print "got end-of-location"
                        return loc.strip(), i + 1 + index
                    else:
                        if c != ' ':
                            loc += c
            
            else:
                raise self.ParseError("parse error at %d. Expected ' Loc.'" % i)
            

        def collect_datetime(n, i):
            if n[i:][:10] == ' Added on ':
                i += 10
                try:
                    end = n[i:].index('\n\n')-10
                except ValueError:
                    end = len(n)
                try:
                    date = datetime.strptime(n[i:][:end], '%A, %d %B %y %H:%M:%S')
                    return date, end+i+12 # skip the two newlines
                except ValueError:
                    raise self.ParseError("unable to parse date string '%s' at location %i. Around there was chars '%s'"
                                          % (n[i:][:end], i, n[i:][:4]))
            else:
                raise self.ParseError("parse error at %d. Expected ' Added on '" % i)
                       

        
        def collect_text(n, i):
            if not n[i:] == "<This item is copy protected>":
                return str(n[i:]), len(n)
            else:
                # damned DRM
                return None, len(n)
                    
            
        # END helper functions

        index = 0
        title, index = collect_title(note, index)
        author, index = collect_author(note, index)
        type, index = collect_note_highlight(note, index)
        location, index = collect_location(note, index)
        date, index = collect_datetime(note, index)
        text, index = collect_text(note, index)

        return {'title': title, 'author': author,
                'type': type, 'location': location,
                'date': date, 'text': text}
