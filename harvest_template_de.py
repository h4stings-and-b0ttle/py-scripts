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

    def __init__(self, generator, templateTitle, fields, param_first, param_debug, param_quick, param_safe):
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
        self.param_quick = param_quick
        self.param_safe = param_safe
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

    def adding(self, item, value, qualif_date, qualif_stats, page):

        claim = pywikibot.Claim(self.repo, 'P54')                
        #value=self.ger_cleaning(value)        
        
        if claim.type == 'wikibase-item':
            # Try to extract a valid page
            linked_item = None
                                    
            #si pas d'article existant pour un élément donné
            #if re.search(r'Estonia U-?15',value): 
            #    linked_item = pywikibot.ItemPage(self.repo, "Q23930638")
            #value = re.sub(r'\[\[([^\[]*) national football team\|[^\|]* U-?([12][0-9])\]\]', r'[[\1 national under-\2 football team]]', value)
            #value = re.sub(r'\[\[([^\[]*) national football team\|[^\|]* Olympics\]\]', r'[[\1 national under-23 football team]]', value)      
            
            #si suspicion d'ajout d'équipe B...           
            if re.search(r'\[[^|]*[^I]\|[^]]* II\]\]',value) or re.search(r'\[[^|]*[^B]\|[^]]* B\]\]',value): 
                pywikibot.output(color_format(
                    '{red}B team ? to check : %s' 
                    % value))
            else:
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
                '%s value after : %s'
                % (claim.getID(), value))
            
        #******** h4stings, nettoyage des qualifiers
        if self.param_debug:
            pywikibot.output('qualifs %s %s'
                %(qualif_date, qualif_stats))
        dates = ''
        nb_matchs = ''
        nb_buts = ''
        wp_debut = ''
        wp_fin = ''
        wp_pret = False
        qualifier_debut = None
        qualifier_fin = None
        qualifier_pret = None
        qualifier_matchs = None
        qualifier_buts = None
            
        #récup info et definition des qualifiers correspondants
        if qualif_date:
            qualif_date = qualif_date.replace ('–', '-')
            qualif_date = qualif_date.replace ('&ndash;', '-')
            qualif_date = re.sub(r'{{0(\|0+)?}}', '', qualif_date)
            qualif_date = re.sub(r'<ref.*<\/ref>', '', qualif_date)
            qualif_date = re.sub(r'<ref.*\/ *>', '', qualif_date)            
            qualif_date = re.sub(r'[a-zA-Zéêû&; \'\.\[\?\]\{\}\|]', '', qualif_date)
            if (qualif_date.find('-') == -1): 
                qualif_date = qualif_date + '-' + qualif_date 
            dates = qualif_date.split('-')

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
            
            if (value.find('Leihe') > -1): 
                wp_pret = True
                qualifier_pret = pywikibot.Claim(self.repo, u'P1642', isQualifier=True)
                qualifier_pret.setTarget( pywikibot.ItemPage(self.repo, "Q2914547"))
                if self.param_debug:
                    pywikibot.output('loan OK')
                        
            #stats
            if qualif_stats:                
                stats = qualif_stats.replace ('–', '-')
                stats = re.sub(r'\(\-[0-9]+\)', '(0)', stats)
                stats = re.sub(r'<ref.*<\/ref>', '', stats)
                stats = re.sub(r'<ref.*\/ *>', '', stats)            
                stats = re.sub(r'[a-zA-Zéêû&; \'\.\[\?\]\{\}\)\|]', '', stats)
                statsT = stats.split("(")
                nb_matchs = statsT[0]
                if len(statsT)>1:
                    nb_buts = statsT[1]
                
                if self.param_debug:
                    pywikibot.output('stats %s / %s / %s'
                        %(statsT, nb_matchs, nb_buts))
                
                if qualifier_fin is not None:
                    if nb_matchs.isdigit():
                        qualifier_matchs = pywikibot.Claim(self.repo, u'P1350', isQualifier=True)
                        qualifier_matchs.setTarget(pywikibot.WbQuantity(amount=nb_matchs, error=0))
                    if nb_buts.isdigit():
                        qualifier_buts = pywikibot.Claim(self.repo, u'P1351', isQualifier=True)
                        qualifier_buts.setTarget(pywikibot.WbQuantity(amount=nb_buts, error=0))
                    if self.param_debug:
                        pywikibot.output('stats %s (%s) OK'
                            % (nb_matchs, nb_buts))
        
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
                    existing1350 = None
                    existing1351 = None
                    qual_added = False
                    wd_debut = None
                    wd_fin = None
                    wd_pret = None
                    wd_matchs = None
                    wd_buts = None
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
                                wd_pret = existing1642[0].getTarget()
                        if qfield.strip() == 'P1350':
                            existing1350 = qvalue
                            if existing1350[0].getTarget() is not None:
                                wd_matchs = existing1350[0].getTarget()
                        if qfield.strip() == 'P1351':
                            existing1351 = qvalue
                            if existing1351[0].getTarget() is not None:
                                wd_buts = existing1351[0].getTarget()
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
                    if self.param_quick and wd_matchs:
                        pywikibot.output('quick skip %s' % value)
                        return

                    #si mêmes qualifiers (ou pas de qualifiers): on passe
                    if (wd_debut == wp_debut or qualifier_debut is None) and (wd_fin == wp_fin or qualifier_fin is None) and (existing1642 is not None or qualifier_pret is None) and (existing1350 is not None or qualifier_matchs is None) and (existing1351 is not None or qualifier_buts is None):
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
                    if qualifier_pret is not None and not existing1642 and (wd_debut == wp_debut) and (wd_fin == wp_fin):
                        existing.addQualifier(qualifier_pret)
                        pywikibot.output(color_format('{green}adding loan as a qualifier of %s'
                            % value))
                        qual_added=True
                    #ajout du qualif nb_matchs si on a une donnée, qu'il y a la place et que dates cohérentes
                    if qualifier_matchs is not None and not existing1350 and (not existing580 or wd_debut == wp_debut) and (not existing582 or wd_fin == wp_fin):
                        existing.addQualifier(qualifier_matchs)
                        pywikibot.output(color_format('{green}adding %s as a nb matchs of %s'
                            % (nb_matchs,value)))
                        qual_added=True
                    #ajout du qualif nb_buts si on a une donnée, qu'il y a la place et que dates cohérentes
                    if qualifier_buts is not None and not existing1351 and (not existing580 or wd_debut == wp_debut) and (not existing582 or wd_fin == wp_fin):
                        existing.addQualifier(qualifier_buts)
                        pywikibot.output(color_format('{green}adding %s as a nb buts of %s'
                            % (nb_buts,value)))
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
                                '{red}Error ? Incohérence détectée : %s' 
                                % value))
                            skip_claim=True
                            break
                                                    
        #******* h4stings, si le club n'est pas dans wikidata : la totale, on se pose pas la question
        if not skip_claim:
            #verif si instance de clubs ou sélection
            if self.param_safe :
                item_to_check = pywikibot.ItemPage(self.repo, claim.getTarget().getID())
                if self.param_debug:
                    pywikibot.output('item to check %s' 
                            % str(claim.getTarget().getID()))
                item_to_check.get() 
                if item_to_check.claims:
                    if 'P31' in item_to_check.claims:
                        claim_nature = item_to_check.claims['P31'] 
                        for existing in claim_nature:
                            if self.param_debug:
                                pywikibot.output('nature %s' 
                                        % str(existing.getTarget().getID()))
                            #if l'item a pour nature un des id acceptés, c'est bon
                            if existing.getTarget().getID() in ['Q476028', 'Q6979593', 'Q21945604', 'Q847017', 'Q12973014', 'Q15944511', 'Q14752149', 'Q6979740', 'Q2367225', 'Q4438121', 'Q18558301', 'Q15896028', 'Q1194951', 'Q23759293', 'Q23904672', 'Q23847779', 'Q23895910', 'Q23901123', 'Q23901137', 'Q23904671', 'Q23904673']:
                            
                                pywikibot.output(color_format('{green}win ! adding %s --> %s : %s, from %s to %s (loan : %s)'
                                                % (claim.getID(), claim.getTarget(), value, wp_debut, wp_fin, wp_pret)))
                                item.addClaim(claim)
                                source = self.getSource(page.site)
                                if source:
                                    claim.addSource(source, bot=True)
                                if qualifier_debut is not None:
                                    claim.addQualifier(qualifier_debut)
                                if qualifier_fin is not None:
                                    claim.addQualifier(qualifier_fin)
                                if qualifier_pret is not None:
                                    claim.addQualifier(qualifier_pret)
                                if qualifier_matchs is not None:
                                    claim.addQualifier(qualifier_matchs)
                                if qualifier_buts is not None:
                                    claim.addQualifier(qualifier_buts)
                                return
                pywikibot.output(color_format('{red}nature of %s is not OK' % claim.getTarget()))                        
        return
        
    def treat(self, page, item):
        
        """Process a single page/item."""
        if willstop:
            raise KeyboardInterrupt
        self.current_page = page
        item.get()
        titre = page.title()
        
        clubs = []
        teams = []
        years = []
        stats = []
        value_stat = ""
        
        #param -b
        if self.param_first is not None:
            if self.param_first in titre:
                self.param_first = None
            else:
                pywikibot.output('Skipping')
                return
                
        pagetext = page.get(False, True)
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
                        
                if fielddict.get("vereine") is not None :
                    if self.param_debug:
                        pywikibot.output(
                            'hastings-test-wp0 clubs %s -> years %s & stats %s' 
                            % (fielddict.get("vereine"), fielddict.get("jahre"), fielddict.get("spiele (tore)")))
                    clubs = re.split("< *br *\/?>", fielddict.get("vereine"))
                    if fielddict.get("jahre") is not None :
                        years = re.split("< *br *\/?>", fielddict.get("jahre"))
                    if fielddict.get("spiele (tore)") is not None :
                        spiele = fielddict.get("spiele (tore)").replace("{{0}}", "")
                        stats = re.split("< *br *\/?>", spiele)

                    if (len(clubs)==len(years)):                    
                        if self.param_debug:
                            pywikibot.output(
                                '%s %s %s' 
                                % (clubs, years, stats))
                        for i in range(0, len(clubs)):
                            if (i<len(stats)):
                                value_stat = stats[i]
                            if self.param_debug:
                                pywikibot.output(
                                    '%s %s %s %s' 
                                    % (i, clubs[i], years[i], value_stat))
                            self.adding(item, clubs[i], years[i], value_stat, page)
                    else:
                        break
                
                if fielddict.get("nationalmannschaft") is not None :
                    if self.param_debug:
                        pywikibot.output(
                            'hastings-test-wp0 teams %s -> years %s & stats %s' 
                            % (fielddict.get("nationalmannschaft"), fielddict.get("nationaljahre"), fielddict.get("länderspiele (tore)")))
                    teams = re.split("< *br *\/?>", fielddict.get("nationalmannschaft"))
                    if fielddict.get("nationaljahre") is not None :
                        years = re.split("< *br *\/?>", fielddict.get("nationaljahre"))
                    if fielddict.get("länderspiele (tore)") is not None :
                        spiele = fielddict.get("länderspiele (tore)").replace("{{0}}", "")
                        stats = re.split("< *br *\/?>", spiele)
                        
                    if (len(teams)==len(years)):
                        for i in range(0, len(teams)):
                            if (i<len(stats)):
                                value_stat = stats[i]
                            if self.param_debug:
                                pywikibot.output(
                                    '%s %s %s %s' 
                                    % (i, teams[i], years[i], value_stat))
                            self.adding(item, teams[i], years[i], value_stat, page)
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
    template_title = u'Infobox Fußballspieler'

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen = pg.GeneratorFactory()

    param_debug = False
    param_first = None
    # quick : si on trouve une stat on skippe l'élément (déjà vu)
    param_quick = False
    # safe : vérifier nature des équipes ajoutées
    param_safe = False
    
    for arg in local_args:
        if arg == '-d':
            param_debug = True
        elif arg == '-quick':
            param_quick = True
        elif arg == '-safe':
            param_safe = True
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

    bot = HarvestRobot(generator, template_title, fields, param_first, param_debug, param_quick, param_safe)
    bot.run()

if __name__ == "__main__":
    main()
