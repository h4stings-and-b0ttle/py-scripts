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

docuReplacements = {'&params;': pywikibot.pagegenerators.parameterHelp}


class HarvestRobot(WikidataBot):

    """A bot to add Wikidata claims."""

    def __init__(self, generator, templateTitle, fields):
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
        # TODO: Make it a list which also includes the redirects to the template
        self.fields = fields
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
#test désactivé par h4stings pour le cas des footeux (P54 multiple)
#       if set(self.fields.values()) <= set(item.claims.keys()): 
#           pywikibot.output('%s item %s has claims for all properties. '
#                            'Skipping.' % (page, item.title()))
#           return

        pagetext = page.get()
        # h4stings on vire les tableaux entraîneur
        pagetext = re.sub(r'carrière entraîneur *= *{{trois colonnes', r'carrière entraîneur = {{Pouet', pagetext)        
        templates = textlib.extract_templates_and_params(pagetext)
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
                for field, value in fielddict.items():
                    field = field.strip()
                    value = value.strip()
                    if not field or not value:
                        continue
#                    pywikibot.output(
#                        'hastings-test0 %s -> %s (%s)' 
#                        % (field, value, int(field) % 3))
                    # dans 3 colonnes Le champ précédant la value contient le qualifier 
                    #if field not in self.fields:
                    if int(field) % 3 == 1:
                        qualif = value
                    # This field contains something useful for us
                    #else:
                    elif int(field) % 3 == 2:
                        fieldm = int(field) % 3
                        claim = pywikibot.Claim(self.repo, self.fields[str(fieldm)])
                        
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

                        pywikibot.output(
                            'hastings-test1 %s field %s value %s'
                            % (claim.getID(), field, value))
                            
                        #******** h4stings, mise en forme des qualifiers
                        qualif = qualif.replace ('[', '')
                        qualif = qualif.replace ('–', '-')
                        #si pas de tiret, 
                        if (qualif.find('-') == -1): 
                            qualif = qualif + '-' + qualif 
                        dates = qualif.split('-')
                        qualifier_debut = None
                        qualifier_fin = None
                        if dates[0]:
                            date1=dates[0][:4]
                            qualifier_debut = pywikibot.Claim(self.repo, u'P580', isQualifier=True)
                            qualifier_debut.setTarget(pywikibot.WbTime(year=date1))
                            pywikibot.output(' fr %s'
                                % qualifier_debut.getTarget().toTimestr())
                        if dates[1]:
                            date2=dates[1][:4]
                            qualifier_fin = pywikibot.Claim(self.repo, u'P582', isQualifier=True)
                            qualifier_fin.setTarget(pywikibot.WbTime(year=date2))
                            pywikibot.output(' to %s'
                                % qualifier_fin.getTarget().toTimestr())

                        existing_claims = item.claims[claim.getID()]  # Existing claims on page of same property
                        skip = False
                        
                        for existing in existing_claims:
                            existing580 = None
                            existing582 = None
                            
                            # If some attribute of the claim being added matches some attribute in an existing claim
                            # of the same property, skip the claim, unless the 'exists' argument overrides it.
                            if claim.getTarget() == existing.getTarget():
                                
                                #******** on va chercher les qualifiers :
                                for qfield, qvalue in existing.qualifiers.items():
                                    if qfield.strip() == 'P580':
                                        existing580 = qvalue
                                    if qfield.strip() == 'P582':
                                        existing582 = qvalue
                                if existing580 is not None:
                                    pywikibot.output('fr %s '
                                        % existing580[0].getTarget().toTimestr())
                                if existing582 is not None:
                                    pywikibot.output(' to %s'
                                        % existing582[0].getTarget().toTimestr())
                                        
                                #si existant sans qualif -> on ajoute les qualif
                                if not existing580 and not existing582:
                                    if dates[0]:
                                        existing.addQualifier(qualifier_debut)
                                        pywikibot.output('adding %s as a qualifier'
                                            % date1)
                                    if dates[1]:
                                        existing.addQualifier(qualifier_fin)
                                        pywikibot.output('adding %s as a qualifier'
                                            % date2)
                                    skip=True
                                    break
                                
                                #sinon, même qualifier : on passe (skip=true)
                                elif qualifier_debut.getTarget() == existing580[0].getTarget() and qualifier_fin.getTarget() == existing582[0].getTarget():
                                    pywikibot.output(
                                        'Skipping %s because claim with same target already exists.' 
                                        % claim.getID())
                                    skip=True
                                    break
                                    
                                #sinon, si les dates ne se chevauchent pas, on envisage la création...
                                elif qualifier_debut.getTarget().toTimestr() >= existing582[0].getTarget().toTimestr() or qualifier_fin.getTarget().toTimestr() <= existing580[0].getTarget().toTimestr():
                                    skip=False
                                    
                                #sinon, c'est bizarre : on logue. 
                                else:
                                    pywikibot.output(
                                        'Vérifier les qualifiers de %s' 
                                        % claim.getID())
                                    pywikibot.log(
                                        'Vérifier les qualifiers de %s' 
                                        % claim.getID())
                                    skip=True
                                                                    
                        #******* h4stings, si le club n'est pas dans wikidata : la totale, on se pose pas la question
                        if not skip:
                            pywikibot.output('Adding %s --> %s, from %s to %s'
                                             % (claim.getID(), claim.getTarget(), date1, date2))
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
    template_title = u''

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen = pg.GeneratorFactory()

    for arg in local_args:
        if arg.startswith('-template'):
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

    bot = HarvestRobot(generator, template_title, fields)
    bot.run()

if __name__ == "__main__":
    main()
