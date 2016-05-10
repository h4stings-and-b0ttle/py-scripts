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
#https://www.wikidata.org/wiki/User:Underlying_lk/remove_claims.py
#https://github.com/wikimedia/pywikibot-core/blob/master/tests/wikibase_edit_tests.py

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

    def __init__(self, generator, templateTitle, fields, param_first, param_debug, param_quick, param_safe, param_clean):
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
        self.param_clean = param_clean
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

    def cleaning(self, item, value, page):

        claim = pywikibot.Claim(self.repo, 'P54')
        
        if claim.type == 'wikibase-item':
            # Try to extract a valid page
            linked_item = None
            
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
                
        #on regarde ce qu'il y a dans le P54
        remove = list()
        if claim.getID() in item.claims:
            existing_claims = item.claims[claim.getID()]  # Existing claims on page of same property       
                
            for existing in existing_claims:
                # si on retrouve dans WD le club de l'infobox, on supprime
                if claim.getTarget().getID() == existing.getTarget().getID():
                    #item.removeClaims(item.claims['P54'])
                    #claimclaim = pywikibot.Claim(repo, u'P54')
                    #theitem = pywikibot.ItemPage(repo, claim.getTarget())
                    #claimclaim.setTarget(theitem)
                    #item.removeClaims(claim.getTarget().getID())
                    remove.append(existing)
                
            if remove:
                item.removeClaims(remove)            
                pywikibot.output(color_format('{yellow}removing %s --> %s : %s'
                                % (claim.getID(), claim.getTarget(), value)))
                return
        return
            
    def adding(self, item, value, qualif, page):

        claim = pywikibot.Claim(self.repo, 'P54')                
        #value=self.ger_cleaning(value)        
        
        if claim.type == 'wikibase-item':
            # Try to extract a valid page
            linked_item = None
            
            #si utilisation du modèle fb
            if re.search(r'{{fb',value):
                value=self.nft_cleaning(value)
            
            #si pas d'article existant pour un élément donné
            #if re.search(r'Estonia U-?15',value): 
            #    linked_item = pywikibot.ItemPage(self.repo, "Q23930638")      
            
            value = re.sub(r'\[\[([^\[\|0-9]*) national football team\|[^\|\]0-9]* U-?([12][0-9])\]\]', r'[[\1 national under-\2 football team]]', value)
            value = re.sub(r'\[\[([^\[\|0-9]*) national football team\|[^\|\]0-9]* Olympics\]\]', r'[[\1 national under-23 football team]]', value)      
                
            #si suspicion d'ajout d'équipe B...           
            if re.search(r'\|[A-Za-z \-`\']* B\]\]',value): 
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
            pywikibot.output('qualif %s'
                % qualif)
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
        if qualif:
            qualif_tab = qualif.split('|')
            #date
            qualif_date = qualif_tab[0]
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
            
            if (value.find('loan') > -1): 
                wp_pret = True
                qualifier_pret = pywikibot.Claim(self.repo, u'P1642', isQualifier=True)
                qualifier_pret.setTarget( pywikibot.ItemPage(self.repo, "Q2914547"))
                if self.param_debug:
                    pywikibot.output('loan OK')
                        
            #stats       
            if len(qualif_tab)>1:
                nb_matchs = qualif_tab[1]
            if len(qualif_tab)>2:
                nb_buts = qualif_tab[2]
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

                    #si mêmes qualifiers : on passe
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
                    if qualifier_pret is not None and not existing1642 and (not existing580 or wd_debut == wp_debut) and (not existing582 or wd_fin == wp_fin):
                        existing.addQualifier(qualifier_pret)
                        pywikibot.output(color_format('{green}adding loan as a qualifier of %s'
                            % value))
                        qual_added=True
                    #ajout du qualif nb_matchs si on a une donnée, qu'il y a la place et que dates cohérentes
                    if qualifier_matchs is not None and not existing1350 and (wd_debut == wp_debut and wd_fin == wp_fin or qual_added):
                        existing.addQualifier(qualifier_matchs)
                        pywikibot.output(color_format('{green}adding %s as a nb matchs of %s'
                            % (nb_matchs,value)))
                        qual_added=True
                    #ajout du qualif nb_buts si on a une donnée, qu'il y a la place et que dates cohérentes
                    if qualifier_buts is not None and not existing1351 and (wd_debut == wp_debut and wd_fin == wp_fin or qual_added):
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
        
    def nft_cleaning(self, pagetext):
        
        pagetext = pagetext.replace('{{fb|Afghanistan}}', '[[Afghanistan national football team]]')
        pagetext = pagetext.replace('{{fb|AFG}}', '[[Afghanistan national football team]]')
        pagetext = pagetext.replace('{{fb|Albania}}', '[[Albania national football team]]')
        pagetext = pagetext.replace('{{fb|ALB}}', '[[Albania national football team]]')
        pagetext = pagetext.replace('{{fb|Algeria}}', '[[Algeria national football team]]')
        pagetext = pagetext.replace('{{fb|ALG}}', '[[Algeria national football team]]')
        pagetext = pagetext.replace('{{fb|American Samoa}}', '[[American Samoa national football team]]')
        pagetext = pagetext.replace('{{fb|ASA}}', '[[American Samoa national football team]]')
        pagetext = pagetext.replace('{{fb|Andorra}}', '[[Andorra national football team]]')
        pagetext = pagetext.replace('{{fb|AND}}', '[[Andorra national football team]]')
        pagetext = pagetext.replace('{{fb|Angola}}', '[[Angola national football team]]')
        pagetext = pagetext.replace('{{fb|ANG}}', '[[Angola national football team]]')
        pagetext = pagetext.replace('{{fb|Anguilla}}', '[[Anguilla national football team]]')
        pagetext = pagetext.replace('{{fb|AIA}}', '[[Anguilla national football team]]')
        pagetext = pagetext.replace('{{fb|Antigua and Barbuda}}', '[[Antigua and Barbuda national football team]]')
        pagetext = pagetext.replace('{{fb|ATG}}', '[[Antigua and Barbuda national football team]]')
        pagetext = pagetext.replace('{{fb|Argentina}}', '[[Argentina national football team]]')
        pagetext = pagetext.replace('{{fb|ARG}}', '[[Argentina national football team]]')
        pagetext = pagetext.replace('{{fb|Armenia}}', '[[Armenia national football team]]')
        pagetext = pagetext.replace('{{fb|ARM}}', '[[Armenia national football team]]')
        pagetext = pagetext.replace('{{fb|Aruba}}', '[[Aruba national football team]]')
        pagetext = pagetext.replace('{{fb|ARU}}', '[[Aruba national football team]]')
        pagetext = pagetext.replace('{{fb|Australia}}', '[[Australia national football team]]')
        pagetext = pagetext.replace('{{fb|AUS}}', '[[Australia national football team]]')
        pagetext = pagetext.replace('{{fb|Austria}}', '[[Austria national football team]]')
        pagetext = pagetext.replace('{{fb|AUT}}', '[[Austria national football team]]')
        pagetext = pagetext.replace('{{fb|Azerbaijan}}', '[[Azerbaijan national football team]]')
        pagetext = pagetext.replace('{{fb|AZE}}', '[[Azerbaijan national football team]]')
        pagetext = pagetext.replace('{{fb|Bahamas}}', '[[Bahamas national football team]]')
        pagetext = pagetext.replace('{{fb|BAH}}', '[[Bahamas national football team]]')
        pagetext = pagetext.replace('{{fb|Bahrain}}', '[[Bahrain national football team]]')
        pagetext = pagetext.replace('{{fb|BHR}}', '[[Bahrain national football team]]')
        pagetext = pagetext.replace('{{fb|Bangladesh}}', '[[Bangladesh national football team]]')
        pagetext = pagetext.replace('{{fb|BAN}}', '[[Bangladesh national football team]]')
        pagetext = pagetext.replace('{{fb|Barbados}}', '[[Barbados national football team]]')
        pagetext = pagetext.replace('{{fb|BRB}}', '[[Barbados national football team]]')
        pagetext = pagetext.replace('{{fb|Belarus}}', '[[Belarus national football team]]')
        pagetext = pagetext.replace('{{fb|BLR}}', '[[Belarus national football team]]')
        pagetext = pagetext.replace('{{fb|Belgium}}', '[[Belgium national football team]]')
        pagetext = pagetext.replace('{{fb|BEL}}', '[[Belgium national football team]]')
        pagetext = pagetext.replace('{{fb|Belize}}', '[[Belize national football team]]')
        pagetext = pagetext.replace('{{fb|BLZ}}', '[[Belize national football team]]')
        pagetext = pagetext.replace('{{fb|Benin}}', '[[Benin national football team]]')
        pagetext = pagetext.replace('{{fb|BEN}}', '[[Benin national football team]]')
        pagetext = pagetext.replace('{{fb|Bermuda}}', '[[Bermuda national football team]]')
        pagetext = pagetext.replace('{{fb|BER}}', '[[Bermuda national football team]]')
        pagetext = pagetext.replace('{{fb|Bhutan}}', '[[Bhutan national football team]]')
        pagetext = pagetext.replace('{{fb|BHU}}', '[[Bhutan national football team]]')
        pagetext = pagetext.replace('{{fb|Bolivia}}', '[[Bolivia national football team]]')
        pagetext = pagetext.replace('{{fb|BOL}}', '[[Bolivia national football team]]')
        pagetext = pagetext.replace('{{fb|Bosnia and Herzegovina}}', '[[Bosnia and Herzegovina national football team]]')
        pagetext = pagetext.replace('{{fb|BIH}}', '[[Bosnia and Herzegovina national football team]]')
        pagetext = pagetext.replace('{{fb|Botswana}}', '[[Botswana national football team]]')
        pagetext = pagetext.replace('{{fb|BOT}}', '[[Botswana national football team]]')
        pagetext = pagetext.replace('{{fb|Brazil}}', '[[Brazil national football team]]')
        pagetext = pagetext.replace('{{fb|BRA}}', '[[Brazil national football team]]')
        pagetext = pagetext.replace('{{fb|British Virgin Islands}}', '[[British Virgin Islands national football team]]')
        pagetext = pagetext.replace('{{fb|VGB}}', '[[British Virgin Islands national football team]]')
        pagetext = pagetext.replace('{{fb|Brunei}}', '[[Brunei national football team]]')
        pagetext = pagetext.replace('{{fb|BRU}}', '[[Brunei national football team]]')
        pagetext = pagetext.replace('{{fb|Bulgaria}}', '[[Bulgaria national football team]]')
        pagetext = pagetext.replace('{{fb|BUL}}', '[[Bulgaria national football team]]')
        pagetext = pagetext.replace('{{fb|Burkina Faso}}', '[[Burkina Faso national football team]]')
        pagetext = pagetext.replace('{{fb|BFA}}', '[[Burkina Faso national football team]]')
        pagetext = pagetext.replace('{{fb|Burundi}}', '[[Burundi national football team]]')
        pagetext = pagetext.replace('{{fb|BDI}}', '[[Burundi national football team]]')
        pagetext = pagetext.replace('{{fb|Cambodia}}', '[[Cambodia national football team]]')
        pagetext = pagetext.replace('{{fb|CAM}}', '[[Cambodia national football team]]')
        pagetext = pagetext.replace('{{fb|Cameroon}}', '[[Cameroon national football team]]')
        pagetext = pagetext.replace('{{fb|CMR}}', '[[Cameroon national football team]]')
        pagetext = pagetext.replace('{{fb|Canada}}', '[[Canada national football team]]')
        pagetext = pagetext.replace('{{fb|CAN}}', '[[Canada national football team]]')
        pagetext = pagetext.replace('{{fb|Cape Verde}}', '[[Cape Verde national football team]]')
        pagetext = pagetext.replace('{{fb|CPV}}', '[[Cape Verde national football team]]')
        pagetext = pagetext.replace('{{fb|Cayman Islands}}', '[[Cayman Islands national football team]]')
        pagetext = pagetext.replace('{{fb|CAY}}', '[[Cayman Islands national football team]]')
        pagetext = pagetext.replace('{{fb|Central African Republic}}', '[[Central African Republic national football team]]')
        pagetext = pagetext.replace('{{fb|CTA}}', '[[Central African Republic national football team]]')
        pagetext = pagetext.replace('{{fb|Chad}}', '[[Chad national football team]]')
        pagetext = pagetext.replace('{{fb|CHA}}', '[[Chad national football team]]')
        pagetext = pagetext.replace('{{fb|Chile}}', '[[Chile national football team]]')
        pagetext = pagetext.replace('{{fb|CHI}}', '[[Chile national football team]]')
        pagetext = pagetext.replace('{{fb|China PR}}', '[[China PR national football team]]')
        pagetext = pagetext.replace('{{fb|CHN}}', '[[China PR national football team]]')
        pagetext = pagetext.replace('{{fb|Chinese Taipei}}', '[[Chinese Taipei national football team]]')
        pagetext = pagetext.replace('{{fb|TPE}}', '[[Chinese Taipei national football team]]')
        pagetext = pagetext.replace('{{fb|Colombia}}', '[[Colombia national football team]]')
        pagetext = pagetext.replace('{{fb|COL}}', '[[Colombia national football team]]')
        pagetext = pagetext.replace('{{fb|Comoros}}', '[[Comoros national football team]]')
        pagetext = pagetext.replace('{{fb|COM}}', '[[Comoros national football team]]')
        pagetext = pagetext.replace('{{fb|Congo}}', '[[Congo national football team]]')
        pagetext = pagetext.replace('{{fb|CGO}}', '[[Congo national football team]]')
        pagetext = pagetext.replace('{{fb|DR Congo}}', '[[DR Congo national football team]]')
        pagetext = pagetext.replace('{{fb|COD}}', '[[DR Congo national football team]]')
        pagetext = pagetext.replace('{{fb|Cook Islands}}', '[[Cook Islands national football team]]')
        pagetext = pagetext.replace('{{fb|COK}}', '[[Cook Islands national football team]]')
        pagetext = pagetext.replace('{{fb|Costa Rica}}', '[[Costa Rica national football team]]')
        pagetext = pagetext.replace('{{fb|CRC}}', '[[Costa Rica national football team]]')
        pagetext = pagetext.replace('{{fb|Croatia}}', '[[Croatia national football team]]')
        pagetext = pagetext.replace('{{fb|CRO}}', '[[Croatia national football team]]')
        pagetext = pagetext.replace('{{fb|Cuba}}', '[[Cuba national football team]]')
        pagetext = pagetext.replace('{{fb|CUB}}', '[[Cuba national football team]]')
        pagetext = pagetext.replace('{{fb|Curaçao}}', '[[Curaçao national football team]]')
        pagetext = pagetext.replace('{{fb|CUW}}', '[[Curaçao national football team]]')
        pagetext = pagetext.replace('{{fb|Country}}', '[[Country national football team]]')
        pagetext = pagetext.replace('{{fb|Code}}', '[[Country national football team]]')
        pagetext = pagetext.replace('{{fb|Cyprus}}', '[[Cyprus national football team]]')
        pagetext = pagetext.replace('{{fb|CYP}}', '[[Cyprus national football team]]')
        pagetext = pagetext.replace('{{fb|Czech Republic}}', '[[Czech Republic national football team]]')
        pagetext = pagetext.replace('{{fb|CZE}}', '[[Czech Republic national football team]]')
        pagetext = pagetext.replace('{{fb|Denmark}}', '[[Denmark national football team]]')
        pagetext = pagetext.replace('{{fb|DEN}}', '[[Denmark national football team]]')
        pagetext = pagetext.replace('{{fb|Djibouti}}', '[[Djibouti national football team]]')
        pagetext = pagetext.replace('{{fb|DJI}}', '[[Djibouti national football team]]')
        pagetext = pagetext.replace('{{fb|Dominica}}', '[[Dominica national football team]]')
        pagetext = pagetext.replace('{{fb|DMA}}', '[[Dominica national football team]]')
        pagetext = pagetext.replace('{{fb|Dominican Republic}}', '[[Dominican Republic national football team]]')
        pagetext = pagetext.replace('{{fb|DOM}}', '[[Dominican Republic national football team]]')
        pagetext = pagetext.replace('{{fb|Ecuador}}', '[[Ecuador national football team]]')
        pagetext = pagetext.replace('{{fb|ECU}}', '[[Ecuador national football team]]')
        pagetext = pagetext.replace('{{fb|Egypt}}', '[[Egypt national football team]]')
        pagetext = pagetext.replace('{{fb|EGY}}', '[[Egypt national football team]]')
        pagetext = pagetext.replace('{{fb|El Salvador}}', '[[El Salvador national football team]]')
        pagetext = pagetext.replace('{{fb|SLV}}', '[[El Salvador national football team]]')
        pagetext = pagetext.replace('{{fb|England}}', '[[England national football team]]')
        pagetext = pagetext.replace('{{fb|ENG}}', '[[England national football team]]')
        pagetext = pagetext.replace('{{fb|Equatorial Guinea}}', '[[Equatorial Guinea national football team]]')
        pagetext = pagetext.replace('{{fb|EQG}}', '[[Equatorial Guinea national football team]]')
        pagetext = pagetext.replace('{{fb|Eritrea}}', '[[Eritrea national football team]]')
        pagetext = pagetext.replace('{{fb|ERI}}', '[[Eritrea national football team]]')
        pagetext = pagetext.replace('{{fb|Estonia}}', '[[Estonia national football team]]')
        pagetext = pagetext.replace('{{fb|EST}}', '[[Estonia national football team]]')
        pagetext = pagetext.replace('{{fb|Ethiopia}}', '[[Ethiopia national football team]]')
        pagetext = pagetext.replace('{{fb|ETH}}', '[[Ethiopia national football team]]')
        pagetext = pagetext.replace('{{fb|Faroe Islands}}', '[[Faroe Islands national football team]]')
        pagetext = pagetext.replace('{{fb|FRO}}', '[[Faroe Islands national football team]]')
        pagetext = pagetext.replace('{{fb|Fiji}}', '[[Fiji national football team]]')
        pagetext = pagetext.replace('{{fb|FIJ}}', '[[Fiji national football team]]')
        pagetext = pagetext.replace('{{fb|Finland}}', '[[Finland national football team]]')
        pagetext = pagetext.replace('{{fb|FIN}}', '[[Finland national football team]]')
        pagetext = pagetext.replace('{{fb|France}}', '[[France national football team]]')
        pagetext = pagetext.replace('{{fb|FRA}}', '[[France national football team]]')
        pagetext = pagetext.replace('{{fb|Gabon}}', '[[Gabon national football team]]')
        pagetext = pagetext.replace('{{fb|GAB}}', '[[Gabon national football team]]')
        pagetext = pagetext.replace('{{fb|Gambia}}', '[[Gambia national football team]]')
        pagetext = pagetext.replace('{{fb|GAM}}', '[[Gambia national football team]]')
        pagetext = pagetext.replace('{{fb|Georgia}}', '[[Georgia national football team]]')
        pagetext = pagetext.replace('{{fb|GEO}}', '[[Georgia national football team]]')
        pagetext = pagetext.replace('{{fb|Germany}}', '[[Germany national football team]]')
        pagetext = pagetext.replace('{{fb|GER}}', '[[Germany national football team]]')
        pagetext = pagetext.replace('{{fb|Ghana}}', '[[Ghana national football team]]')
        pagetext = pagetext.replace('{{fb|GHA}}', '[[Ghana national football team]]')
        pagetext = pagetext.replace('{{fb|Greece}}', '[[Greece national football team]]')
        pagetext = pagetext.replace('{{fb|GRE}}', '[[Greece national football team]]')
        pagetext = pagetext.replace('{{fb|Grenada}}', '[[Grenada national football team]]')
        pagetext = pagetext.replace('{{fb|GRN}}', '[[Grenada national football team]]')
        pagetext = pagetext.replace('{{fb|Guam}}', '[[Guam national football team]]')
        pagetext = pagetext.replace('{{fb|GUM}}', '[[Guam national football team]]')
        pagetext = pagetext.replace('{{fb|Guatemala}}', '[[Guatemala national football team]]')
        pagetext = pagetext.replace('{{fb|GUA}}', '[[Guatemala national football team]]')
        pagetext = pagetext.replace('{{fb|Guinea}}', '[[Guinea national football team]]')
        pagetext = pagetext.replace('{{fb|GUI}}', '[[Guinea national football team]]')
        pagetext = pagetext.replace('{{fb|Guinea-Bissau}}', '[[Guinea-Bissau national football team]]')
        pagetext = pagetext.replace('{{fb|GNB}}', '[[Guinea-Bissau national football team]]')
        pagetext = pagetext.replace('{{fb|Guyana}}', '[[Guyana national football team]]')
        pagetext = pagetext.replace('{{fb|GUY}}', '[[Guyana national football team]]')
        pagetext = pagetext.replace('{{fb|Haiti}}', '[[Haiti national football team]]')
        pagetext = pagetext.replace('{{fb|HAI}}', '[[Haiti national football team]]')
        pagetext = pagetext.replace('{{fb|Honduras}}', '[[Honduras national football team]]')
        pagetext = pagetext.replace('{{fb|HON}}', '[[Honduras national football team]]')
        pagetext = pagetext.replace('{{fb|Hong Kong}}', '[[Hong Kong national football team]]')
        pagetext = pagetext.replace('{{fb|HKG}}', '[[Hong Kong national football team]]')
        pagetext = pagetext.replace('{{fb|Hungary}}', '[[Hungary national football team]]')
        pagetext = pagetext.replace('{{fb|HUN}}', '[[Hungary national football team]]')
        pagetext = pagetext.replace('{{fb|Iceland}}', '[[Iceland national football team]]')
        pagetext = pagetext.replace('{{fb|ISL}}', '[[Iceland national football team]]')
        pagetext = pagetext.replace('{{fb|India}}', '[[India national football team]]')
        pagetext = pagetext.replace('{{fb|IND}}', '[[India national football team]]')
        pagetext = pagetext.replace('{{fb|Indonesia}}', '[[Indonesia national football team]]')
        pagetext = pagetext.replace('{{fb|IDN}}', '[[Indonesia national football team]]')
        pagetext = pagetext.replace('{{fb|Iran}}', '[[Iran national football team]]')
        pagetext = pagetext.replace('{{fb|IRN}}', '[[Iran national football team]]')
        pagetext = pagetext.replace('{{fb|Iraq}}', '[[Iraq national football team]]')
        pagetext = pagetext.replace('{{fb|IRQ}}', '[[Iraq national football team]]')
        pagetext = pagetext.replace('{{fb|Israel}}', '[[Israel national football team]]')
        pagetext = pagetext.replace('{{fb|ISR}}', '[[Israel national football team]]')
        pagetext = pagetext.replace('{{fb|Italy}}', '[[Italy national football team]]')
        pagetext = pagetext.replace('{{fb|ITA}}', '[[Italy national football team]]')
        pagetext = pagetext.replace('{{fb|Ivory Coast}}', '[[Ivory Coast national football team]]')
        pagetext = pagetext.replace('{{fb|CIV}}', '[[Ivory Coast national football team]]')
        pagetext = pagetext.replace('{{fb|Jamaica}}', '[[Jamaica national football team]]')
        pagetext = pagetext.replace('{{fb|JAM}}', '[[Jamaica national football team]]')
        pagetext = pagetext.replace('{{fb|Japan}}', '[[Japan national football team]]')
        pagetext = pagetext.replace('{{fb|JPN}}', '[[Japan national football team]]')
        pagetext = pagetext.replace('{{fb|Jordan}}', '[[Jordan national football team]]')
        pagetext = pagetext.replace('{{fb|JOR}}', '[[Jordan national football team]]')
        pagetext = pagetext.replace('{{fb|Kazakhstan}}', '[[Kazakhstan national football team]]')
        pagetext = pagetext.replace('{{fb|KAZ}}', '[[Kazakhstan national football team]]')
        pagetext = pagetext.replace('{{fb|Kenya}}', '[[Kenya national football team]]')
        pagetext = pagetext.replace('{{fb|KEN}}', '[[Kenya national football team]]')
        pagetext = pagetext.replace('{{fb|Kuwait}}', '[[Kuwait national football team]]')
        pagetext = pagetext.replace('{{fb|KUW}}', '[[Kuwait national football team]]')
        pagetext = pagetext.replace('{{fb|Kyrgyzstan}}', '[[Kyrgyzstan national football team]]')
        pagetext = pagetext.replace('{{fb|KGZ}}', '[[Kyrgyzstan national football team]]')
        pagetext = pagetext.replace('{{fb|Laos}}', '[[Laos national football team]]')
        pagetext = pagetext.replace('{{fb|LAO}}', '[[Laos national football team]]')
        pagetext = pagetext.replace('{{fb|Latvia}}', '[[Latvia national football team]]')
        pagetext = pagetext.replace('{{fb|LVA}}', '[[Latvia national football team]]')
        pagetext = pagetext.replace('{{fb|Lebanon}}', '[[Lebanon national football team]]')
        pagetext = pagetext.replace('{{fb|LIB}}', '[[Lebanon national football team]]')
        pagetext = pagetext.replace('{{fb|Country}}', '[[Country national football team]]')
        pagetext = pagetext.replace('{{fb|Code}}', '[[Country national football team]]')
        pagetext = pagetext.replace('{{fb|Lesotho}}', '[[Lesotho national football team]]')
        pagetext = pagetext.replace('{{fb|LES}}', '[[Lesotho national football team]]')
        pagetext = pagetext.replace('{{fb|Liberia}}', '[[Liberia national football team]]')
        pagetext = pagetext.replace('{{fb|LBR}}', '[[Liberia national football team]]')
        pagetext = pagetext.replace('{{fb|Libya}}', '[[Libya national football team]]')
        pagetext = pagetext.replace('{{fb|LBY}}', '[[Libya national football team]]')
        pagetext = pagetext.replace('{{fb|Liechtenstein}}', '[[Liechtenstein national football team]]')
        pagetext = pagetext.replace('{{fb|LIE}}', '[[Liechtenstein national football team]]')
        pagetext = pagetext.replace('{{fb|Lithuania}}', '[[Lithuania national football team]]')
        pagetext = pagetext.replace('{{fb|LTU}}', '[[Lithuania national football team]]')
        pagetext = pagetext.replace('{{fb|Luxembourg}}', '[[Luxembourg national football team]]')
        pagetext = pagetext.replace('{{fb|LUX}}', '[[Luxembourg national football team]]')
        pagetext = pagetext.replace('{{fb|Macau}}', '[[Macau national football team]]')
        pagetext = pagetext.replace('{{fb|MAC}}', '[[Macau national football team]]')
        pagetext = pagetext.replace('{{fb|Macedonia}}', '[[Macedonia national football team]]')
        pagetext = pagetext.replace('{{fb|MKD}}', '[[Macedonia national football team]]')
        pagetext = pagetext.replace('{{fb|Madagascar}}', '[[Madagascar national football team]]')
        pagetext = pagetext.replace('{{fb|MAD}}', '[[Madagascar national football team]]')
        pagetext = pagetext.replace('{{fb|Malawi}}', '[[Malawi national football team]]')
        pagetext = pagetext.replace('{{fb|MWI}}', '[[Malawi national football team]]')
        pagetext = pagetext.replace('{{fb|Malaysia}}', '[[Malaysia national football team]]')
        pagetext = pagetext.replace('{{fb|MAS}}', '[[Malaysia national football team]]')
        pagetext = pagetext.replace('{{fb|Maldives}}', '[[Maldives national football team]]')
        pagetext = pagetext.replace('{{fb|MDV}}', '[[Maldives national football team]]')
        pagetext = pagetext.replace('{{fb|Mali}}', '[[Mali national football team]]')
        pagetext = pagetext.replace('{{fb|MLI}}', '[[Mali national football team]]')
        pagetext = pagetext.replace('{{fb|Malta}}', '[[Malta national football team]]')
        pagetext = pagetext.replace('{{fb|MLT}}', '[[Malta national football team]]')
        pagetext = pagetext.replace('{{fb|Mauritania}}', '[[Mauritania national football team]]')
        pagetext = pagetext.replace('{{fb|MTN}}', '[[Mauritania national football team]]')
        pagetext = pagetext.replace('{{fb|Mauritius}}', '[[Mauritius national football team]]')
        pagetext = pagetext.replace('{{fb|MRI}}', '[[Mauritius national football team]]')
        pagetext = pagetext.replace('{{fb|Mexico}}', '[[Mexico national football team]]')
        pagetext = pagetext.replace('{{fb|MEX}}', '[[Mexico national football team]]')
        pagetext = pagetext.replace('{{fb|Moldova}}', '[[Moldova national football team]]')
        pagetext = pagetext.replace('{{fb|MDA}}', '[[Moldova national football team]]')
        pagetext = pagetext.replace('{{fb|Mongolia}}', '[[Mongolia national football team]]')
        pagetext = pagetext.replace('{{fb|MNG}}', '[[Mongolia national football team]]')
        pagetext = pagetext.replace('{{fb|Montenegro}}', '[[Montenegro national football team]]')
        pagetext = pagetext.replace('{{fb|MNE}}', '[[Montenegro national football team]]')
        pagetext = pagetext.replace('{{fb|Montserrat}}', '[[Montserrat national football team]]')
        pagetext = pagetext.replace('{{fb|MSR}}', '[[Montserrat national football team]]')
        pagetext = pagetext.replace('{{fb|Morocco}}', '[[Morocco national football team]]')
        pagetext = pagetext.replace('{{fb|MAR}}', '[[Morocco national football team]]')
        pagetext = pagetext.replace('{{fb|Mozambique}}', '[[Mozambique national football team]]')
        pagetext = pagetext.replace('{{fb|MOZ}}', '[[Mozambique national football team]]')
        pagetext = pagetext.replace('{{fb|Myanmar}}', '[[Myanmar national football team]]')
        pagetext = pagetext.replace('{{fb|MYA}}', '[[Myanmar national football team]]')
        pagetext = pagetext.replace('{{fb|Namibia}}', '[[Namibia national football team]]')
        pagetext = pagetext.replace('{{fb|NAM}}', '[[Namibia national football team]]')
        pagetext = pagetext.replace('{{fb|Nepal}}', '[[Nepal national football team]]')
        pagetext = pagetext.replace('{{fb|NEP}}', '[[Nepal national football team]]')
        pagetext = pagetext.replace('{{fb|Netherlands}}', '[[Netherlands national football team]]')
        pagetext = pagetext.replace('{{fb|NED}}', '[[Netherlands national football team]]')
        pagetext = pagetext.replace('{{fb|New Caledonia}}', '[[New Caledonia national football team]]')
        pagetext = pagetext.replace('{{fb|NCL}}', '[[New Caledonia national football team]]')
        pagetext = pagetext.replace('{{fb|New Zealand}}', '[[New Zealand national football team]]')
        pagetext = pagetext.replace('{{fb|NZL}}', '[[New Zealand national football team]]')
        pagetext = pagetext.replace('{{fb|Nicaragua}}', '[[Nicaragua national football team]]')
        pagetext = pagetext.replace('{{fb|NCA}}', '[[Nicaragua national football team]]')
        pagetext = pagetext.replace('{{fb|Niger}}', '[[Niger national football team]]')
        pagetext = pagetext.replace('{{fb|NIG}}', '[[Niger national football team]]')
        pagetext = pagetext.replace('{{fb|Nigeria}}', '[[Nigeria national football team]]')
        pagetext = pagetext.replace('{{fb|NGA}}', '[[Nigeria national football team]]')
        pagetext = pagetext.replace('{{fb|North Korea}}', '[[North Korea national football team]]')
        pagetext = pagetext.replace('{{fb|PRK}}', '[[North Korea national football team]]')
        pagetext = pagetext.replace('{{fb|Northern Ireland}}', '[[Northern Ireland national football team]]')
        pagetext = pagetext.replace('{{fb|NIR}}', '[[Northern Ireland national football team]]')
        pagetext = pagetext.replace('{{fb|Norway}}', '[[Norway national football team]]')
        pagetext = pagetext.replace('{{fb|NOR}}', '[[Norway national football team]]')
        pagetext = pagetext.replace('{{fb|Oman}}', '[[Oman national football team]]')
        pagetext = pagetext.replace('{{fb|OMA}}', '[[Oman national football team]]')
        pagetext = pagetext.replace('{{fb|Pakistan}}', '[[Pakistan national football team]]')
        pagetext = pagetext.replace('{{fb|PAK}}', '[[Pakistan national football team]]')
        pagetext = pagetext.replace('{{fb|Palestine}}', '[[Palestine national football team]]')
        pagetext = pagetext.replace('{{fb|PLE}}', '[[Palestine national football team]]')
        pagetext = pagetext.replace('{{fb|Panama}}', '[[Panama national football team]]')
        pagetext = pagetext.replace('{{fb|PAN}}', '[[Panama national football team]]')
        pagetext = pagetext.replace('{{fb|Papua New Guinea}}', '[[Papua New Guinea national football team]]')
        pagetext = pagetext.replace('{{fb|PNG}}', '[[Papua New Guinea national football team]]')
        pagetext = pagetext.replace('{{fb|Paraguay}}', '[[Paraguay national football team]]')
        pagetext = pagetext.replace('{{fb|PAR}}', '[[Paraguay national football team]]')
        pagetext = pagetext.replace('{{fb|Peru}}', '[[Peru national football team]]')
        pagetext = pagetext.replace('{{fb|PER}}', '[[Peru national football team]]')
        pagetext = pagetext.replace('{{fb|Philippines}}', '[[Philippines national football team]]')
        pagetext = pagetext.replace('{{fb|PHI}}', '[[Philippines national football team]]')
        pagetext = pagetext.replace('{{fb|Poland}}', '[[Poland national football team]]')
        pagetext = pagetext.replace('{{fb|POL}}', '[[Poland national football team]]')
        pagetext = pagetext.replace('{{fb|Portugal}}', '[[Portugal national football team]]')
        pagetext = pagetext.replace('{{fb|POR}}', '[[Portugal national football team]]')
        pagetext = pagetext.replace('{{fb|Puerto Rico}}', '[[Puerto Rico national football team]]')
        pagetext = pagetext.replace('{{fb|PUR}}', '[[Puerto Rico national football team]]')
        pagetext = pagetext.replace('{{fb|Qatar}}', '[[Qatar national football team]]')
        pagetext = pagetext.replace('{{fb|QAT}}', '[[Qatar national football team]]')
        pagetext = pagetext.replace('{{fb|Republic of Ireland}}', '[[Republic of Ireland national football team]]')
        pagetext = pagetext.replace('{{fb|IRL}}', '[[Republic of Ireland national football team]]')
        pagetext = pagetext.replace('{{fb|Romania}}', '[[Romania national football team]]')
        pagetext = pagetext.replace('{{fb|ROU}}', '[[Romania national football team]]')
        pagetext = pagetext.replace('{{fb|Russia}}', '[[Russia national football team]]')
        pagetext = pagetext.replace('{{fb|RUS}}', '[[Russia national football team]]')
        pagetext = pagetext.replace('{{fb|Rwanda}}', '[[Rwanda national football team]]')
        pagetext = pagetext.replace('{{fb|RWA}}', '[[Rwanda national football team]]')
        pagetext = pagetext.replace('{{fb|Saint Kitts and Nevis}}', '[[Saint Kitts and Nevis national football team]]')
        pagetext = pagetext.replace('{{fb|SKN}}', '[[Saint Kitts and Nevis national football team]]')
        pagetext = pagetext.replace('{{fb|Country}}', '[[Country national football team]]')
        pagetext = pagetext.replace('{{fb|Code}}', '[[Country national football team]]')
        pagetext = pagetext.replace('{{fb|Saint Lucia}}', '[[Saint Lucia national football team]]')
        pagetext = pagetext.replace('{{fb|LCA}}', '[[Saint Lucia national football team]]')
        pagetext = pagetext.replace('{{fb|Saint Vincent and the Grenadines}}', '[[Saint Vincent and the Grenadines national football team]]')
        pagetext = pagetext.replace('{{fb|VIN}}', '[[Saint Vincent and the Grenadines national football team]]')
        pagetext = pagetext.replace('{{fb|Samoa}}', '[[Samoa national football team]]')
        pagetext = pagetext.replace('{{fb|SAM}}', '[[Samoa national football team]]')
        pagetext = pagetext.replace('{{fb|San Marino}}', '[[San Marino national football team]]')
        pagetext = pagetext.replace('{{fb|SMR}}', '[[San Marino national football team]]')
        pagetext = pagetext.replace('{{fb|São Tomé and Príncipe}}', '[[São Tomé and Príncipe national football team]]')
        pagetext = pagetext.replace('{{fb|STP}}', '[[São Tomé and Príncipe national football team]]')
        pagetext = pagetext.replace('{{fb|Saudi Arabia}}', '[[Saudi Arabia national football team]]')
        pagetext = pagetext.replace('{{fb|KSA}}', '[[Saudi Arabia national football team]]')
        pagetext = pagetext.replace('{{fb|Scotland}}', '[[Scotland national football team]]')
        pagetext = pagetext.replace('{{fb|SCO}}', '[[Scotland national football team]]')
        pagetext = pagetext.replace('{{fb|Senegal}}', '[[Senegal national football team]]')
        pagetext = pagetext.replace('{{fb|SEN}}', '[[Senegal national football team]]')
        pagetext = pagetext.replace('{{fb|Serbia}}', '[[Serbia national football team]]')
        pagetext = pagetext.replace('{{fb|SRB}}', '[[Serbia national football team]]')
        pagetext = pagetext.replace('{{fb|Seychelles}}', '[[Seychelles national football team]]')
        pagetext = pagetext.replace('{{fb|SEY}}', '[[Seychelles national football team]]')
        pagetext = pagetext.replace('{{fb|Sierra Leone}}', '[[Sierra Leone national football team]]')
        pagetext = pagetext.replace('{{fb|SLE}}', '[[Sierra Leone national football team]]')
        pagetext = pagetext.replace('{{fb|Singapore}}', '[[Singapore national football team]]')
        pagetext = pagetext.replace('{{fb|SIN}}', '[[Singapore national football team]]')
        pagetext = pagetext.replace('{{fb|Slovakia}}', '[[Slovakia national football team]]')
        pagetext = pagetext.replace('{{fb|SVK}}', '[[Slovakia national football team]]')
        pagetext = pagetext.replace('{{fb|Slovenia}}', '[[Slovenia national football team]]')
        pagetext = pagetext.replace('{{fb|SVN}}', '[[Slovenia national football team]]')
        pagetext = pagetext.replace('{{fb|Solomon Islands}}', '[[Solomon Islands national football team]]')
        pagetext = pagetext.replace('{{fb|SOL}}', '[[Solomon Islands national football team]]')
        pagetext = pagetext.replace('{{fb|Somalia}}', '[[Somalia national football team]]')
        pagetext = pagetext.replace('{{fb|SOM}}', '[[Somalia national football team]]')
        pagetext = pagetext.replace('{{fb|South Africa}}', '[[South Africa national football team]]')
        pagetext = pagetext.replace('{{fb|RSA}}', '[[South Africa national football team]]')
        pagetext = pagetext.replace('{{fb|South Korea}}', '[[South Korea national football team]]')
        pagetext = pagetext.replace('{{fb|KOR}}', '[[South Korea national football team]]')
        pagetext = pagetext.replace('{{fb|South Sudan}}', '[[South Sudan national football team]]')
        pagetext = pagetext.replace('{{fb|SSD}}', '[[South Sudan national football team]]')
        pagetext = pagetext.replace('{{fb|Spain}}', '[[Spain national football team]]')
        pagetext = pagetext.replace('{{fb|ESP}}', '[[Spain national football team]]')
        pagetext = pagetext.replace('{{fb|Sri Lanka}}', '[[Sri Lanka national football team]]')
        pagetext = pagetext.replace('{{fb|SRI}}', '[[Sri Lanka national football team]]')
        pagetext = pagetext.replace('{{fb|Sudan}}', '[[Sudan national football team]]')
        pagetext = pagetext.replace('{{fb|SDN}}', '[[Sudan national football team]]')
        pagetext = pagetext.replace('{{fb|Suriname}}', '[[Suriname national football team]]')
        pagetext = pagetext.replace('{{fb|SUR}}', '[[Suriname national football team]]')
        pagetext = pagetext.replace('{{fb|Swaziland}}', '[[Swaziland national football team]]')
        pagetext = pagetext.replace('{{fb|SWZ}}', '[[Swaziland national football team]]')
        pagetext = pagetext.replace('{{fb|Sweden}}', '[[Sweden national football team]]')
        pagetext = pagetext.replace('{{fb|SWE}}', '[[Sweden national football team]]')
        pagetext = pagetext.replace('{{fb|Switzerland}}', '[[Switzerland national football team]]')
        pagetext = pagetext.replace('{{fb|SUI}}', '[[Switzerland national football team]]')
        pagetext = pagetext.replace('{{fb|Syria}}', '[[Syria national football team]]')
        pagetext = pagetext.replace('{{fb|SYR}}', '[[Syria national football team]]')
        pagetext = pagetext.replace('{{fb|Tahiti}}', '[[Tahiti national football team]]')
        pagetext = pagetext.replace('{{fb|TAH}}', '[[Tahiti national football team]]')
        pagetext = pagetext.replace('{{fb|Tajikistan}}', '[[Tajikistan national football team]]')
        pagetext = pagetext.replace('{{fb|TJK}}', '[[Tajikistan national football team]]')
        pagetext = pagetext.replace('{{fb|Tanzania}}', '[[Tanzania national football team]]')
        pagetext = pagetext.replace('{{fb|TAN}}', '[[Tanzania national football team]]')
        pagetext = pagetext.replace('{{fb|Thailand}}', '[[Thailand national football team]]')
        pagetext = pagetext.replace('{{fb|THA}}', '[[Thailand national football team]]')
        pagetext = pagetext.replace('{{fb|Timor-Leste}}', '[[Timor-Leste national football team]]')
        pagetext = pagetext.replace('{{fb|TLS}}', '[[Timor-Leste national football team]]')
        pagetext = pagetext.replace('{{fb|Togo}}', '[[Togo national football team]]')
        pagetext = pagetext.replace('{{fb|TOG}}', '[[Togo national football team]]')
        pagetext = pagetext.replace('{{fb|Tonga}}', '[[Tonga national football team]]')
        pagetext = pagetext.replace('{{fb|TGA}}', '[[Tonga national football team]]')
        pagetext = pagetext.replace('{{fb|Trinidad and Tobago}}', '[[Trinidad and Tobago national football team]]')
        pagetext = pagetext.replace('{{fb|TRI}}', '[[Trinidad and Tobago national football team]]')
        pagetext = pagetext.replace('{{fb|Tunisia}}', '[[Tunisia national football team]]')
        pagetext = pagetext.replace('{{fb|TUN}}', '[[Tunisia national football team]]')
        pagetext = pagetext.replace('{{fb|Turkey}}', '[[Turkey national football team]]')
        pagetext = pagetext.replace('{{fb|TUR}}', '[[Turkey national football team]]')
        pagetext = pagetext.replace('{{fb|Turkmenistan}}', '[[Turkmenistan national football team]]')
        pagetext = pagetext.replace('{{fb|TKM}}', '[[Turkmenistan national football team]]')
        pagetext = pagetext.replace('{{fb|Turks and Caicos Islands}}', '[[Turks and Caicos Islands national football team]]')
        pagetext = pagetext.replace('{{fb|TCA}}', '[[Turks and Caicos Islands national football team]]')
        pagetext = pagetext.replace('{{fb|Uganda}}', '[[Uganda national football team]]')
        pagetext = pagetext.replace('{{fb|UGA}}', '[[Uganda national football team]]')
        pagetext = pagetext.replace('{{fb|Ukraine}}', '[[Ukraine national football team]]')
        pagetext = pagetext.replace('{{fb|UKR}}', '[[Ukraine national football team]]')
        pagetext = pagetext.replace('{{fb|United Arab Emirates}}', '[[United Arab Emirates national football team]]')
        pagetext = pagetext.replace('{{fb|UAE}}', '[[United Arab Emirates national football team]]')
        pagetext = pagetext.replace('{{fb|United States}}', '[[United States national football team]]')
        pagetext = pagetext.replace('{{fb|USA}}', '[[United States national football team]]')
        pagetext = pagetext.replace('{{fb|Uruguay}}', '[[Uruguay national football team]]')
        pagetext = pagetext.replace('{{fb|URU}}', '[[Uruguay national football team]]')
        pagetext = pagetext.replace('{{fb|U.S. Virgin Islands}}', '[[U.S. Virgin Islands national football team]]')
        pagetext = pagetext.replace('{{fb|VIR}}', '[[U.S. Virgin Islands national football team]]')
        pagetext = pagetext.replace('{{fb|Uzbekistan}}', '[[Uzbekistan national football team]]')
        pagetext = pagetext.replace('{{fb|UZB}}', '[[Uzbekistan national football team]]')
        pagetext = pagetext.replace('{{fb|Vanuatu}}', '[[Vanuatu national football team]]')
        pagetext = pagetext.replace('{{fb|VAN}}', '[[Vanuatu national football team]]')
        pagetext = pagetext.replace('{{fb|Venezuela}}', '[[Venezuela national football team]]')
        pagetext = pagetext.replace('{{fb|VEN}}', '[[Venezuela national football team]]')
        pagetext = pagetext.replace('{{fb|Vietnam}}', '[[Vietnam national football team]]')
        pagetext = pagetext.replace('{{fb|VIE}}', '[[Vietnam national football team]]')
        pagetext = pagetext.replace('{{fb|Wales}}', '[[Wales national football team]]')
        pagetext = pagetext.replace('{{fb|WAL}}', '[[Wales national football team]]')
        pagetext = pagetext.replace('{{fb|Yemen}}', '[[Yemen national football team]]')
        pagetext = pagetext.replace('{{fb|YEM}}', '[[Yemen national football team]]')
        pagetext = pagetext.replace('{{fb|Zambia}}', '[[Zambia national football team]]')
        pagetext = pagetext.replace('{{fb|ZAM}}', '[[Zambia national football team]]')
        pagetext = pagetext.replace('{{fb|Zimbabwe}}', '[[Zimbabwe national football team]]')
        pagetext = pagetext.replace('{{fb|ZIM}}', '[[Zimbabwe national football team]]')

        return pagetext
        
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
        
        value = ""
        qualif = ""
        repopulate = False
                
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
                
                for k in range(1, 10):                            
                    if fielddict.get("nationalteam"+str(k)):
                        value = fielddict["nationalteam"+str(k)]
                        
                        #si sélection nationale mal formatée
                        if self.param_clean or re.search(r'\[\[[^\[\|0-9]* national football team\|[^\|\]0-9]* U-?[12][0-9]\]\]',value) or re.search(r'\[\[[^\[\|0-9]* national football team\|[^\|\]0-9]* Olympics\]\]',value):
                            self.cleaning(item, value, page)
                            repopulate = True
                            break
                    else:
                        break

                #on a supprimé des données, il faut recharger les sélections !
                if repopulate:
                                
                    #item = None
                    item.get(force=True)
                    for j in range(1, 10):
                        value = ""
                        qualif = ""
                        if self.param_debug:
                            pywikibot.output(
                                'hastings-test0 %s -> %s & %s -> %s & %s (%s)' 
                                % ("nationalteam"+str(j), fielddict.get("nationalteam"+str(j)), "nationalyears"+str(j), fielddict.get("nationalyears"+str(j)), fielddict.get("nationalcaps"+str(j)), fielddict.get("nationalgoals"+str(j))))
                                
                        if fielddict.get("nationalteam"+str(j)):
                            value = fielddict["nationalteam"+str(j)]
                            if re.search(r'{{fb',value):
                                value=self.nft_cleaning(value)
                            if fielddict.get("nationalyears"+str(j)):
                                qualif = fielddict["nationalyears"+str(j)]
                            if fielddict.get("nationalcaps"+str(j)):
                                qualif = qualif + "|" + fielddict["nationalcaps"+str(j)]
                            if fielddict.get("nationalgoals"+str(j)):
                                qualif = qualif + "|" + fielddict["nationalgoals"+str(j)]
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
    # quick : si on trouve une stat on skippe l'élément (déjà vu)
    param_quick = False
    # safe : vérifier nature des équipes ajoutées
    param_safe = False
    param_clean = False 
    
    for arg in local_args:
        if arg == '-d':
            param_debug = True
        elif arg == '-quick':
            param_quick = True
        elif arg == '-safe':
            param_safe = True
        elif arg == '-clean':
            param_clean = True
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

    bot = HarvestRobot(generator, template_title, fields, param_first, param_debug, param_quick, param_safe, param_clean)
    bot.run()

if __name__ == "__main__":
    main()
