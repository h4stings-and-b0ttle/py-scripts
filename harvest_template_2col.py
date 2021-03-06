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

    def treat(self, page, item):
        
        """Process a single page/item."""
        if willstop:
            raise KeyboardInterrupt
        self.current_page = page
        item.get()
        titre = page.title()
        
        #param -b
        if self.param_first:
            if self.param_first in titre:
                self.param_first = None
            else:
                pywikibot.output('Skipping')
                return
                
        pagetext = page.get()
        # on met de côté les tableaux entraîneur et junior
        pagetext = re.sub(r'carrière entraîneur *= *{{', 'carrière entraîneur = {{Pouet', pagetext)
        pagetext = re.sub(r'parcours junior *= *{{', 'parcours junior = {{Pouet', pagetext)
        
        if self.param_debug:
            pywikibot.output(
                'self.fields %s' 
                % self.fields)
                
        if self.param_debug:
            pywikibot.log(
                'pagetext : %s' 
                % pagetext)

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
                
                qualif = ""
                for field, value in fielddict.items():
                    field = field.strip()
                    value = value.strip()
                    if not field or not value:
                        continue
                    if self.param_debug:
                        pywikibot.output(
                            'hastings-test0 %s -> %s (%s)' 
                            % (field, value, int(field) % 2))
                    # dans 3 colonnes Le champ précédant la value contient le qualifier 
                    #if field not in self.fields:
                    if int(field) % 2 == 1:
                        qualif = value
                    # This field contains something useful for us
                    #else:
                    elif int(field) % 2 == 0:
                        claim = pywikibot.Claim(self.repo, self.fields["2"])
                        
                        if claim.type == 'wikibase-item':
                            # Try to extract a valid page
                            match = re.search(pywikibot.link_regex, value)
                            if not match:
                                pywikibot.output(
                                    '%s field %s value %s is not a '
                                    'wikilink. Skipping.'
                                    % (claim.getID(), field, value))
                                continue

                            link_text = match.group(1)
                            linked_item = self._template_link_target(item, link_text)
                            if not linked_item:
                                continue

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
                                continue
                            claim.setTarget(image)
                        else:
                            pywikibot.output(
                                '%s is not a supported datatype.'
                                % claim.type)
                            continue

                        if self.param_debug:
                            pywikibot.output(
                                '%s field %s value : %s'
                                % (claim.getID(), field, value))
                            
                        #******** h4stings, nettoyage des qualifiers
                        qualif = qualif.replace ('–', '-')
                        qualif = qualif.replace ('avant ', '-')
                        qualif = qualif.replace ('{{Clr}}', '')
                        qualif = qualif.replace ('{{Year|', '')
                        qualif = qualif.replace ('{{prêt}}', '')
                        qualif = re.sub(r'{{0(\|0+)?}}', '', qualif)
                        qualif = re.sub(r'[a-zA-Zéû&; \.\[\?\]]', '', qualif)
                        #si pas de tiret, 
                        if (qualif.find('-') == -1): 
                            qualif = qualif + '-' + qualif 
                        dates = qualif.split('-')
                        wp_debut = None
                        wp_fin = None
                        qualifier_debut = None
                        qualifier_fin = None
                        if dates[0]:
                            wp_debut = dates[0][:4]
                            qualifier_debut = pywikibot.Claim(self.repo, u'P580', isQualifier=True)
                            qualifier_debut.setTarget(pywikibot.WbTime(year=wp_debut))
                            if self.param_debug:
                                pywikibot.output(' from %s'
                                    % qualifier_debut.getTarget().toTimestr())
                        if dates[1]:
                            wp_fin = dates[1][:4]
                            qualifier_fin = pywikibot.Claim(self.repo, u'P582', isQualifier=True)
                            qualifier_fin.setTarget(pywikibot.WbTime(year=wp_fin))
                            if self.param_debug:
                                pywikibot.output(' to %s'
                                    % qualifier_fin.getTarget().toTimestr())

                        skip = False
                            
                        if claim.getID() in item.claims:
                            existing_claims = item.claims[claim.getID()]  # Existing claims on page of same property
                            skip = False
                
                            for existing in existing_claims:
                                existing580 = None
                                existing582 = None
                                
                                # If some attribute of the claim being added matches some attribute in an existing claim
                                # of the same property, skip the claim, unless the 'exists' argument overrides it.
                                if claim.getTarget() == existing.getTarget():
                                    
                                    #******** on va chercher les qualifiers existants :
                                    wd_debut = None
                                    wd_fin = None
                                    for qfield, qvalue in existing.qualifiers.items():
                                        if qfield.strip() == 'P580':
                                            existing580 = qvalue
                                            wd_debut = existing580[0].getTarget().toTimestr()[8:12]
                                        if qfield.strip() == 'P582':
                                            existing582 = qvalue
                                            wd_fin = existing582[0].getTarget().toTimestr()[8:12]                                        
                                    if self.param_debug:
                                        if existing580 is not None:
                                            pywikibot.output('from %s -> %s'
                                                % (existing580[0].getTarget().toTimestr(), wd_debut))
                                        if existing582 is not None:
                                            pywikibot.output(' to %s -> %s'
                                                % (existing582[0].getTarget().toTimestr(), wd_fin))
                                    
                                    #si existant sans qualif -> on ajoute les qualif
                                    if not existing580 and not existing582:
                                        if dates[0]:
                                            existing.addQualifier(qualifier_debut)
                                            pywikibot.output(color_format('{green}adding %s as a qualifier of %s'
                                                % (wp_debut,value)))
                                        if dates[1]:
                                            existing.addQualifier(qualifier_fin)
                                            pywikibot.output(color_format('{green}adding %s as a qualifier of %s'
                                                % (wp_fin,value)))
                                        skip=True
                                        break
                                    
                                    #sinon, même qualifier : on passe (skip=true)
                                    elif wd_debut == wp_debut and qualifier_fin is None:
                                        pywikibot.output(
                                            'Skipping %s because claim with same target already exists.' 
                                            % value)
                                        skip=True
                                        break

                                    elif qualifier_debut is None and wd_fin == wp_fin:
                                        pywikibot.output(
                                            'Skipping %s because claim with same target already exists.' 
                                            % value)
                                        skip=True
                                        break
                                    elif wd_debut == wp_debut and wd_fin == wp_fin:
                                        pywikibot.output(
                                            'Skipping %s because claim with same target already exists.' 
                                            % value)
                                        skip=True
                                        break
                                        
                                    #sinon, si les dates ne se chevauchent pas, on envisage la création...
                                    elif wp_debut >= wd_fin or wp_fin <= wd_debut: 
                                        pywikibot.output('maybe %s'
                                             % value)
                                        skip=False
                                        
                                    #sinon, c'est bizarre : on signale. 
                                    else:
                                        pywikibot.output(color_format(
                                            '{red}Error ? Incohérence détectée : %s %s %s' 
                                            % (claim.getID(), field, value)))
                                        skip=True
                                                                    
                        #******* h4stings, si le club n'est pas dans wikidata : la totale, on se pose pas la question
                        if not skip:
                            pywikibot.output(color_format('{green}adding %s --> %s : %s, from %s to %s'
                                             % (claim.getID(), claim.getTarget(), value, wp_debut, wp_fin)))
                            item.addClaim(claim)
                            # A generator might yield pages from multiple languages
                            source = self.getSource(page.site)
                            if source:
                                claim.addSource(source, bot=True)
                            if dates[0]:
                                claim.addQualifier(qualifier_debut)
                            if dates[1]:
                                claim.addQualifier(qualifier_fin)
def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    commandline_arguments = list()
    template_title = u'Deux colonnes'

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
