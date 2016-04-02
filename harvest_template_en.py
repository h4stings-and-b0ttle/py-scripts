#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
Template harvesting script. 
edited by h4astings, inspired by claimit.py and others scripts

"""
#
# (C) Multichill, Amir, 2013
# (C) Pywikibot team, 2013-2014
#
# Distributed under the terms of MIT License.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id: 5d07bf562a9faa0bb5467506e8d86cec96558210 $'
#

import re
import signal

willstop = False

def _signal_handler(signal, frame):
    global willstop
    if not willstop:
        willstop = True
        print("Received ctrl-c. Finishing current item; press ctrl-c again to abort.")
    else:
        raise KeyboardInterrupt

signal.signal(signal.SIGINT, _signal_handler)

import pywikibot
from pywikibot import pagegenerators as pg, textlib, WikidataBot
from pywikibot.tools.formatter import color_format

docuReplacements = {'&params;': pywikibot.pagegenerators.parameterHelp}

class HarvestRobot(WikidataBot):

    """A bot to add Wikidata claims."""

    def __init__(self, generator, templateTitle, fields, param_first, param_debug):
        """
        Constructor.

        Arguments:
            * generator     - A generator that yields Page objects.
            * templateTitle - The template to work on
            * fields        - A dictionary of fields that are of use to us

        """
        super(HarvestRobot, self).__init__()
        self.generator = pg.PreloadingGenerator(generator)
        self.templateTitle = templateTitle.replace(u'_', u' ')
        self.fields = fields
        self.param_first = param_first
        self.param_debug = param_debug
        self.cacheSources()
        self.templateTitles = self.getTemplateSynonyms(self.templateTitle)

    def getTemplateSynonyms(self, title):
        """Fetch redirects of the title, so we can check against them."""
        temp = pywikibot.Page(pywikibot.Site(), title, ns=10)
        if not temp.exists():
            pywikibot.error(u'Template %s does not exist.' % temp.title())
            exit()

        # Put some output here since it can take a while
        pywikibot.output('Finding redirects...')
        if temp.isRedirectPage():
            temp = temp.getRedirectTarget()
        titles = [page.title(withNamespace=False)
                  for page in temp.getReferences(redirectsOnly=True, namespaces=[10],
                                                 follow_redirects=False)]
        titles.append(temp.title(withNamespace=False))
        return titles

    def _template_link_target(self, item, link_text):
        linked_page = None

        link = pywikibot.Link(link_text)
        linked_page = pywikibot.Page(link)

        if not linked_page.exists():
            pywikibot.output('%s does not exist so it cannot be linked. '
                             'Skipping.' % (linked_page))
            return

        if linked_page.isRedirectPage():
            linked_page = linked_page.getRedirectTarget()

        try:
            linked_item = pywikibot.ItemPage.fromPage(linked_page)
        except pywikibot.NoPage:
            linked_item = None

        if not linked_item or not linked_item.exists():
            pywikibot.output('%s does not have a wikidata item to link with. '
                             'Skipping.' % (linked_page))
            return

        if linked_item.title() == item.title():
            pywikibot.output('%s links to itself. Skipping.' % (linked_page))
            return

        return linked_item

    def adding(self, item, value, qualif, page):

        claim = pywikibot.Claim(self.repo, 'P54')
        if claim.type == 'wikibase-item':
            # Try to extract a valid page
            match = re.search(pywikibot.link_regex, value)
            if not match:
                pywikibot.output(
                    '%s value %s is not a '
                    'wikilink. Skipping.'
                    % (claim.getID(), value))
                return

            link_text = match.group(1)
            linked_item = self._template_link_target(item, link_text)
            if not linked_item:
                return

            claim.setTarget(linked_item)
        elif claim.type == 'string':
            claim.setTarget(value.strip())
        elif claim.type == 'commonsMedia':
            commonssite = pywikibot.Site("commons", "commons")
            imagelink = pywikibot.Link(value, source=commonssite,
                                       defaultNamespace=6)
            image = pywikibot.FilePage(imagelink)
            if image.isRedirectPage():
                image = pywikibot.FilePage(image.getRedirectTarget())
            if not image.exists():
                pywikibot.output(
                    '[[%s]] doesn\'t exist so I can\'t link to it'
                    % (image.title(),))
                return
            claim.setTarget(image)
        else:
            pywikibot.output(
                '%s is not a supported datatype.'
                % claim.type)
            return

        if self.param_debug:
            pywikibot.output(
                '%s value : %s'
                % (claim.getID(), value))
            
        #******** h4stings, nettoyage des qualifiers
        if qualif:
            qualif = qualif.replace ('–', '-')
            qualif = qualif.replace ('&ndash;', '-')
            qualif = re.sub(r'{{0(\|0+)?}}', '', qualif)
            qualif = re.sub(r'<ref.*<\/ref>', '', qualif)
            qualif = re.sub(r'<ref.*\/ *>', '', qualif)            
            qualif = re.sub(r'[a-zA-Zéêû&; \'\.\[\?\]\{\}\|]', '', qualif)
        #si pas de tiret, 
        if (qualif.find('-') == -1): 
            qualif = qualif + '-' + qualif 
        dates = qualif.split('-')

        #récup info et definition des qualifiers correspondants
        wp_debut = ''
        wp_fin = ''
        wp_pret = False
        qualifier_debut = None
        qualifier_fin = None
        qualifier_pret = None

        if dates[0]:
            wp_debut = dates[0][:4]
            if wp_debut.isdigit():
                if len(wp_debut)==4:
                    qualifier_debut = pywikibot.Claim(self.repo, u'P580', isQualifier=True)
                    qualifier_debut.setTarget(pywikibot.WbTime(year=wp_debut))
                    if self.param_debug:
                        pywikibot.output(' from %s'
                            % qualifier_debut.getTarget().toTimestr())
                            
                    if dates[1]:
                        wp_fin = dates[1][:4]
                        if wp_fin.isdigit():
                            if len(wp_fin)==4:
                                qualifier_fin = pywikibot.Claim(self.repo, u'P582', isQualifier=True)
                                qualifier_fin.setTarget(pywikibot.WbTime(year=wp_fin))
                                if self.param_debug:
                                    pywikibot.output(' to %s'
                                        % qualifier_fin.getTarget().toTimestr())
                            else:
                                pywikibot.output('date fin ignorée : %s %s'
                                    % (value, dates[1]))
                                wp_fin = ''
                        else:
                            pywikibot.output(
                                'incohérence %s : %s'
                                % (value, dates[1]))
                else:
                    pywikibot.output('date début ignorée : %s %s'
                        % (value, dates[0]))
                    wp_debut = ''
            else:
                pywikibot.output(
                    'incohérence %s : %s'
                    % (value, dates[0]))
        
        if (value.find('loan') > -1): 
            wp_pret = True
            qualifier_pret = pywikibot.Claim(self.repo, u'P1642', isQualifier=True)
            qualifier_pret.setTarget( pywikibot.ItemPage(self.repo, "Q2914547"))
            if self.param_debug:
                pywikibot.output('loan OK')
        
        #on regarde ce qu'il y a dans le P54
        skip_claim = False
        if claim.getID() in item.claims:
            existing_claims = item.claims[claim.getID()]  # Existing claims on page of same property
            for existing in existing_claims:

                # si on retrouve dans WD le club de l'infobox (ça devient intéressant)
                if claim.getTarget() == existing.getTarget():
                    # on récupère les qualifiers dans WD
                    existing580 = None
                    existing582 = None
                    existing1642 = None
                    qual_added = False
                    wd_debut = None
                    wd_fin = None
                    wd_pret = None
                    for qfield, qvalue in existing.qualifiers.items():
                        if qfield.strip() == 'P580':
                            existing580 = qvalue
                            if existing580[0].getTarget() is not None:
                                wd_debut = existing580[0].getTarget().toTimestr()[8:12]
                        if qfield.strip() == 'P582':
                            existing582 = qvalue
                            if existing582[0].getTarget() is not None:
                                wd_fin = existing582[0].getTarget().toTimestr()[8:12]
                        if qfield.strip() == 'P1642':
                            existing1642 = qvalue
                            if existing1642[0].getTarget() is not None:
                                wd_pret = existing582[0].getTarget()
                    if self.param_debug:
                        if existing580 is not None:
                            pywikibot.output('from %s -> %s'
                                % (existing580[0].getTarget().toTimestr(), wd_debut))
                        if existing582 is not None:
                            pywikibot.output(' to %s -> %s'
                                % (existing582[0].getTarget().toTimestr(), wd_fin))
                        if existing1642 is not None:
                            pywikibot.output(' loan %s -> %s'
                                % (existing1642[0].getTarget(), wd_pret))

                    #si mêmes qualifiers : on passe
                    if (wd_debut == wp_debut or qualifier_debut is None) and (wd_fin == wp_fin or qualifier_fin is None) and (existing1642 is not None or qualifier_pret is None):
                        pywikibot.output(
                            'Skipping %s because claim with same target already exists.' 
                            % value)
                        skip_claim=True
                        break

                    #ajout du qualif debut si on a une donnée à mettre, qu'il y a la place et date de fin cohérente
                    if qualifier_debut is not None and not existing580 and (not existing582 or wd_fin == wp_fin):
                        existing.addQualifier(qualifier_debut)
                        pywikibot.output(color_format('{green}adding %s as a qualifier of %s'
                            % (wp_debut,value)))
                        qual_added=True
                    #ajout du qualif fin si on a une donnée, qu'il y a la place et que date de début cohérente
                    if qualifier_fin is not None and not existing582 and (not existing580 or wd_debut == wp_debut):
                        existing.addQualifier(qualifier_fin)
                        pywikibot.output(color_format('{green}adding %s as a qualifier of %s'
                            % (wp_fin,value)))
                        qual_added=True
                    #ajout du qualif prêt si on a une donnée, qu'il y a la place et que dates cohérentes
                    if qualifier_pret is not None and not existing1642 and (wd_debut == wp_debut and wd_fin == wp_fin or qual_added):
                        existing.addQualifier(qualifier_pret)
                        pywikibot.output(color_format('{green}adding loan as a qualifier of %s'
                            % value))
                        qual_added=True
                        
                    if qual_added:
                        skip_claim=True
                        break
                    else:
                        #si les dates WD sont différentes, on continue la recherche
                        if wp_debut >= wd_fin or wp_fin <= wd_debut: 
                            pywikibot.output('maybe %s'
                                 % value)
                            
                        #sinon (si les dates WP/WD se chevauchent), on signale 
                        else:
                            pywikibot.output(color_format(
                                '{red}Error ? Incohérence détectée : %s %s' 
                                % (claim.getID(), value)))
                            skip_claim=True
                            break
                                                    
        #******* h4stings, si le club n'est pas dans wikidata : la totale, on se pose pas la question
        if not skip_claim:
            pywikibot.output(color_format('{green}adding %s --> %s : %s, from %s to %s (loan : %s)'
                             % (claim.getID(), claim.getTarget(), value, wp_debut, wp_fin, wp_pret)))
            item.addClaim(claim)
            # A generator might yield pages from multiple languages
            source = self.getSource(page.site)
            if source:
                claim.addSource(source, bot=True)
            if qualifier_debut is not None:
                claim.addQualifier(qualifier_debut)
            if qualifier_fin is not None:
                claim.addQualifier(qualifier_fin)
            if qualifier_pret is not None:
                claim.addQualifier(qualifier_pret)
        
        return
    
    def treat(self, page, item):
        
        """Process a single page/item."""
        if willstop:
            raise KeyboardInterrupt
        self.current_page = page
        item.get()
        titre = page.title()
        
        #param -b
        if self.param_first is not None:
            if self.param_first in titre:
                self.param_first = None
            else:
                pywikibot.output('Skipping')
                return
                
        pagetext = page.get()
        # on met de côté les tableaux entraîneur et junior

        if self.param_debug:
            pywikibot.output(
                'self.fields %s' 
                % self.fields)

        templates = textlib.extract_templates_and_params(pagetext)
        if self.param_debug:
            pywikibot.log(
                'templates : %s' 
                % templates)   
        
        for (template, fielddict) in templates:
            # Clean up template
            try:
                template = pywikibot.Page(page.site, template,
                                          ns=10).title(withNamespace=False)
            except pywikibot.exceptions.InvalidTitle:
                pywikibot.error(
                    "Failed parsing template; '%s' should be the template name."
                    % template)
                continue

            # We found the template we were looking for
            if template in self.templateTitles:

                #nettoyage du fielddict
                for field, value in fielddict.items():
                    field_stripd = field.strip()
                    value_stripd = value.strip()
                    del fielddict[field]
                    fielddict[field_stripd] = value_stripd
                    
                if self.param_debug:
                    pywikibot.output(
                        'hastings-test-wp0 %s' 
                        % fielddict)

                for i in range(1, 40):
                    value = ""
                    qualif = ""
                    if self.param_debug:
                        pywikibot.output(
                            'hastings-test-wp0 %s -> %s & %s -> %s' 
                            % ("clubs"+str(i), fielddict.get("clubs"+str(i)), "years"+str(i), fielddict.get("years"+str(i))))
                            
                    if fielddict.get("clubs"+str(i)):
                        value = fielddict["clubs"+str(i)]
                        if fielddict.get("years"+str(i)):
                            qualif = fielddict["years"+str(i)]
                        self.adding(item, value, qualif, page)
                    else:
                        break
                        
                for j in range(1, 10):
                    value = ""
                    qualif = ""
                    if self.param_debug:
                        pywikibot.output(
                            'hastings-test0 %s -> %s & %s -> %s' 
                            % ("clubs"+str(j), fielddict.get("clubs"+str(j)), "years"+str(j), fielddict.get("years"+str(j))))
                            
                    if fielddict.get("nationalteam"+str(j)):
                        value = fielddict["nationalteam"+str(j)]
                        if fielddict.get("nationalyears"+str(j)):
                            qualif = fielddict["nationalyears"+str(j)]
                        self.adding(item, value, qualif, page)
                    else:
                        break

def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    commandline_arguments = list()
    template_title = u'Infobox football biography'

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen = pg.GeneratorFactory()

    param_debug = False
    param_first = None
    
    for arg in local_args:
        if arg == '-d':
            param_debug = True
        elif arg.startswith('-b'):
            param_first = arg[3:]
        elif arg.startswith('-template'):
            if len(arg) == 9:
                template_title = pywikibot.input(
                    u'Please enter the template to work on:')
            else:
                template_title = arg[10:]
        elif gen.handleArg(arg):
            if arg.startswith(u'-transcludes:'):
                template_title = arg[13:]
        else:
            commandline_arguments.append(arg)

    if not template_title:
        pywikibot.error('Please specify either -template or -transcludes argument')
        return

    if len(commandline_arguments) % 2:
        raise ValueError  # or something.
        
    fields = dict()
    for i in range(0, len(commandline_arguments), 2): 
        fields[commandline_arguments[i]] = commandline_arguments[i + 1]

    generator = gen.getCombinedGenerator()
    if not generator:
        gen.handleArg(u'-transcludes:' + template_title)
        generator = gen.getCombinedGenerator()

    bot = HarvestRobot(generator, template_title, fields, param_first, param_debug)
    bot.run()

if __name__ == "__main__":
    main()
