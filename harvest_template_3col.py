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

    def __init__(self, generator, templateTitle, fields, param_first, param_debug, param_amateur):
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
        self.param_amateur = param_amateur
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

    def nettoyage_selections(self, pagetext):

        pagetext = pagetext.replace('{{FRA football}}', '[[Équipe de France de football|France]]')
        pagetext = pagetext.replace('{{AFG football}}', '[[Équipe d\'Afghanistan de football|Afghanistan]]')
        pagetext = pagetext.replace('{{AHO football}}', '[[Équipe des Antilles néerlandaises de football|Antilles néerlandaises]]')
        pagetext = pagetext.replace('{{AIA football}}', '[[Équipe d\'Anguilla de football|Anguilla]]')
        pagetext = pagetext.replace('{{ALB football -21}}', '[[Équipe d\'Albanie espoirs de football|Albanie]]')
        pagetext = pagetext.replace('{{ALB football}}', '[[Équipe d\'Albanie de football|Albanie]]')
        pagetext = pagetext.replace('{{ALG football -21}}', '[[Équipe d\'Algérie espoirs de football|Algérie]]')
        pagetext = pagetext.replace('{{ALG football}}', '[[Équipe d\'Algérie de football|Algérie]]')
        pagetext = pagetext.replace('{{AND football -21}}', '[[Équipe d\'Andorre espoirs de football|Andorre]]')
        pagetext = pagetext.replace('{{AND football}}', '[[Équipe d\'Andorre de football|Andorre]]')
        pagetext = pagetext.replace('{{ANG football}}', '[[Équipe d\'Angola de football|Angola]]')
        pagetext = pagetext.replace('{{ANT football}}', '[[Équipe d\'Antigua-et-Barbuda de football|Antigua-et-Barbuda]]')
        pagetext = pagetext.replace('{{ARG football -21}}', '[[Équipe d\'Argentine espoirs de football|Argentine]]')
        pagetext = pagetext.replace('{{ARG football}}', '[[Équipe d\'Argentine de football|Argentine]]')
        pagetext = pagetext.replace('{{ARM football -21}}', '[[Équipe d\'Arménie espoirs de football|Arménie]]')
        pagetext = pagetext.replace('{{ARM football}}', '[[Équipe d\'Arménie de football|Arménie]]')
        pagetext = pagetext.replace('{{ARU football}}', '[[Équipe d\'Aruba de football|Aruba]]')
        pagetext = pagetext.replace('{{ASA football}}', '[[Équipe des Samoa américaines de football|Samoa américaines]]')
        pagetext = pagetext.replace('{{AUS football}}', '[[Équipe d\'Australie de football|Australie]]')
        pagetext = pagetext.replace('{{AUT football -21}}', '[[Équipe d\'Autriche espoirs de football|Autriche]]')
        pagetext = pagetext.replace('{{AUT football}}', '[[Équipe d\'Autriche de football|Autriche]]')
        pagetext = pagetext.replace('{{AZE football -21}}', '[[Équipe d\'Azerbaïdjan espoirs de football|Azerbaïdjan]]')
        pagetext = pagetext.replace('{{AZE football}}', '[[Équipe d\'Azerbaïdjan de football|Azerbaïdjan]]')
        pagetext = pagetext.replace('{{BAH football}}', '[[Équipe des Bahamas de football|Bahamas]]')
        pagetext = pagetext.replace('{{BAN football}}', '[[Équipe du Bangladesh de football|Bangladesh]]')
        pagetext = pagetext.replace('{{BAR football}}', '[[Équipe de la Barbade de football|Barbade]]')
        pagetext = pagetext.replace('{{BDI football}}', '[[Équipe du Burundi de football|Burundi]]')
        pagetext = pagetext.replace('{{BEL football}}', '[[Équipe de Belgique de football|Belgique]]')
        pagetext = pagetext.replace('{{BEN football}}', '[[Équipe du Bénin de football|Bénin]]')
        pagetext = pagetext.replace('{{BER football}}', '[[Équipe des Bermudes de football|Bermudes]]')
        pagetext = pagetext.replace('{{BHU football}}', '[[Équipe du Bhoutan de football|Bhoutan]]')
        pagetext = pagetext.replace('{{BIH football -21}}', '[[Équipe de Bosnie-Herzégovine espoirs de football|Bosnie-Herzégovine]]')
        pagetext = pagetext.replace('{{BIH football}}', '[[Équipe de Bosnie-Herzégovine de football|Bosnie-Herzégovine]]')
        pagetext = pagetext.replace('{{BIZ football}}', '[[Équipe du Belize de football|Belize]]')
        pagetext = pagetext.replace('{{BLR football -21}}', '[[Équipe de Biélorussie espoirs de football|Biélorussie]]')
        pagetext = pagetext.replace('{{BLR football}}', '[[Équipe de Biélorussie de football|Biélorussie]]')
        pagetext = pagetext.replace('{{BOL football}}', '[[Équipe de Bolivie de football|Bolivie]]')
        pagetext = pagetext.replace('{{BOT football}}', '[[Équipe du Botswana de football|Botswana]]')
        pagetext = pagetext.replace('{{BRA football}}', '[[Équipe du Brésil de football|Brésil]]')
        pagetext = pagetext.replace('{{BRN football}}', '[[Équipe de Bahreïn de football|Bahreïn]]')
        pagetext = pagetext.replace('{{BRU football}}', '[[Équipe de Brunei de football|Brunei]]')
        pagetext = pagetext.replace('{{BUL football -21}}', '[[Équipe de Bulgarie espoirs de football|Bulgarie]]')
        pagetext = pagetext.replace('{{BUL football}}', '[[Équipe de Bulgarie de football|Bulgarie]]')
        pagetext = pagetext.replace('{{BUR football}}', '[[Équipe du Burkina Faso de football|Burkina Faso]]')
        pagetext = pagetext.replace('{{CAF football}}', '[[Équipe de République centrafricaine de football|République centrafricaine]]')
        pagetext = pagetext.replace('{{CAM football}}', '[[Équipe du Cambodge de football|Cambodge]]')
        pagetext = pagetext.replace('{{CAN football}}', '[[Équipe du Canada de soccer|Canada]]')
        pagetext = pagetext.replace('{{CAY football}}', '[[Équipe des îles Caïmans de football|Îles Caïmans]]')
        pagetext = pagetext.replace('{{CGO football}}', '[[Équipe du Congo de football|Congo]]')
        pagetext = pagetext.replace('{{CHA football}}', '[[Équipe du Tchad de football|Tchad]]')
        pagetext = pagetext.replace('{{CHI football -21}}', '[[Équipe du Chili espoirs de football|Chili]]')
        pagetext = pagetext.replace('{{CHI football}}', '[[Équipe du Chili de football|Chili]]')
        pagetext = pagetext.replace('{{CHN football -21}}', '[[Équipe de Chine espoirs de football|Chine]]')
        pagetext = pagetext.replace('{{CHN football}}', '[[Équipe de Chine de football|Chine]]')
        pagetext = pagetext.replace('{{CIV football}}', '[[Équipe de Côte d\'Ivoire de football|Côte d’Ivoire]]')
        pagetext = pagetext.replace('{{CMR football}}', '[[Équipe du Cameroun de football|Cameroun]]')
        pagetext = pagetext.replace('{{COD football}}', '[[Équipe de République démocratique du Congo de football|Rép. dém. du Congo]]')
        pagetext = pagetext.replace('{{COK football}}', '[[Équipe des îles Cook de football|Îles Cook]]')
        pagetext = pagetext.replace('{{COL football}}', '[[Équipe de Colombie de football|Colombie]]')
        pagetext = pagetext.replace('{{COM football}}', '[[Équipe des Comores de football|Comores]]')
        pagetext = pagetext.replace('{{CPV football}}', '[[Équipe du Cap-Vert de football|Cap-Vert]]')
        pagetext = pagetext.replace('{{CRC football}}', '[[Équipe du Costa Rica de football|Costa Rica]]')
        pagetext = pagetext.replace('{{CRO football -21}}', '[[Équipe de Croatie espoirs de football|Croatie]]')
        pagetext = pagetext.replace('{{CRO football}}', '[[Équipe de Croatie de football|Croatie]]')
        pagetext = pagetext.replace('{{CUB football}}', '[[Équipe de Cuba de football|Cuba]]')
        pagetext = pagetext.replace('{{CYP football -21}}', '[[Équipe de Chypre espoirs de football|Chypre]]')
        pagetext = pagetext.replace('{{CYP football}}', '[[Équipe de Chypre de football|Chypre]]')
        pagetext = pagetext.replace('{{CZE football -21}}', '[[Équipe de République tchèque espoirs de football|République tchèque]]')
        pagetext = pagetext.replace('{{CZE football}}', '[[Équipe de République tchèque de football|République tchèque]]')
        pagetext = pagetext.replace('{{DEN football -21}}', '[[Équipe du Danemark espoirs de football|Danemark]]')
        pagetext = pagetext.replace('{{DEN football}}', '[[Équipe du Danemark de football|Danemark]]')
        pagetext = pagetext.replace('{{DJI football}}', '[[Équipe de Djibouti de football|Djibouti]]')
        pagetext = pagetext.replace('{{DMA football}}', '[[Équipe de Dominique de football|Dominique]]')
        pagetext = pagetext.replace('{{DOM football}}', '[[Équipe de République dominicaine de football|République dominicaine]]')
        pagetext = pagetext.replace('{{ECU football}}', '[[Équipe d\'Équateur de football|Équateur]]')
        pagetext = pagetext.replace('{{EGY football -21}}', '[[Équipe d\'Égypte espoirs de football|Égypte]]')
        pagetext = pagetext.replace('{{EGY football}}', '[[Équipe d\'Égypte de football|Égypte]]')
        pagetext = pagetext.replace('{{ENG football -21}}', '[[Équipe d\'Angleterre espoirs de football|Angleterre]]')
        pagetext = pagetext.replace('{{ENG football}}', '[[Équipe d\'Angleterre de football|Angleterre]]')
        pagetext = pagetext.replace('{{ERI football}}', '[[Équipe d\'Érythrée de football|Érythrée]]')
        pagetext = pagetext.replace('{{ESA football}}', '[[Équipe du Salvador de football|Salvador]]')
        pagetext = pagetext.replace('{{ESP football -21}}', '[[Équipe d\'Espagne espoirs de football|Espagne]]')
        pagetext = pagetext.replace('{{ESP football}}', '[[Équipe d\'Espagne de football|Espagne]]')
        pagetext = pagetext.replace('{{EST football -21}}', '[[Équipe d\'Estonie espoirs de football|Estonie]]')
        pagetext = pagetext.replace('{{EST football}}', '[[Équipe d\'Estonie de football|Estonie]]')
        pagetext = pagetext.replace('{{ETH football}}', '[[Équipe d\'Éthiopie de football|Éthiopie]]')
        pagetext = pagetext.replace('{{FIJ football}}', '[[Équipe des Fidji de football|Fidji]]')
        pagetext = pagetext.replace('{{FIN football -21}}', '[[Équipe de Finlande espoirs de football|Finlande]]')
        pagetext = pagetext.replace('{{FIN football}}', '[[Équipe de Finlande de football|Finlande]]')
        pagetext = pagetext.replace('{{FRA football -21}}', '[[Équipe de France espoirs de football|France]]')
        pagetext = pagetext.replace('{{FRO football -21}}', '[[Équipe des Îles Féroé espoirs de football|Îles Féroé]]')
        pagetext = pagetext.replace('{{FRO football}}', '[[Équipe des îles Féroé de football|Îles Féroé]]')
        pagetext = pagetext.replace('{{GAB football}}', '[[Équipe du Gabon de football|Gabon]]')
        pagetext = pagetext.replace('{{GAM football}}', '[[Équipe de Gambie de football|Gambie]]')
        pagetext = pagetext.replace('{{GBS football}}', '[[Équipe de Guinée-Bissau de football|Guinée-Bissau]]')
        pagetext = pagetext.replace('{{GEO football -21}}', '[[Équipe de Géorgie espoirs de football|Géorgie]]')
        pagetext = pagetext.replace('{{GEO football}}', '[[Équipe de Géorgie de football|Géorgie]]')
        pagetext = pagetext.replace('{{GEQ football}}', '[[Équipe de Guinée équatoriale de football|Guinée équatoriale]]')
        pagetext = pagetext.replace('{{GER football -21}}', '[[Équipe d\'Allemagne espoirs de football|Allemagne]]')
        pagetext = pagetext.replace('{{GER football}}', '[[Équipe d\'Allemagne de football|Allemagne]]')
        pagetext = pagetext.replace('{{GHA football}}', '[[Équipe du Ghana de football|Ghana]]')
        pagetext = pagetext.replace('{{GRE football -21}}', '[[Équipe de Grèce espoirs de football|Grèce]]')
        pagetext = pagetext.replace('{{GRE football}}', '[[Équipe de Grèce de football|Grèce]]')
        pagetext = pagetext.replace('{{GRN football}}', '[[Équipe de Grenade de football|Grenade]]')
        pagetext = pagetext.replace('{{GUA football}}', '[[Équipe du Guatemala de football|Guatemala]]')
        pagetext = pagetext.replace('{{GUI football}}', '[[Équipe de Guinée de football|Guinée]]')
        pagetext = pagetext.replace('{{GUM football}}', '[[Équipe de Guam de football|Guam]]')
        pagetext = pagetext.replace('{{GUY football}}', '[[Équipe du Guyana de football|Guyana]]')
        pagetext = pagetext.replace('{{HAI football}}', '[[Équipe d\'Haïti de football|Haïti]]')
        pagetext = pagetext.replace('{{HKG football}}', '[[Équipe de Hong Kong de football|Hong Kong]]') 
        pagetext = pagetext.replace('{{HON football}}', '[[Équipe du Honduras de football|Honduras]]')
        pagetext = pagetext.replace('{{HUN football -21}}', '[[Équipe de Hongrie espoirs de football|Hongrie]]')
        pagetext = pagetext.replace('{{HUN football}}', '[[Équipe de Hongrie de football|Hongrie]]')
        pagetext = pagetext.replace('{{INA football}}', '[[Équipe d\'Indonésie de football|Indonésie]]')
        pagetext = pagetext.replace('{{IND football}}', '[[Équipe d\'Inde de football|Inde]]')
        pagetext = pagetext.replace('{{IRI football}}', '[[Équipe d\'Iran de football|Iran]]')
        pagetext = pagetext.replace('{{IRL football -21}}', '[[Équipe de République d\'Irlande espoirs de football|Irlande]]')
        pagetext = pagetext.replace('{{IRL football}}', '[[Équipe de République d\'Irlande de football|Irlande]]')
        pagetext = pagetext.replace('{{IRQ football}}', '[[Équipe d\'Irak de football|Irak]]')
        pagetext = pagetext.replace('{{ISL football -21}}', '[[Équipe d\'Islande espoirs de football|Islande]]')
        pagetext = pagetext.replace('{{ISL football}}', '[[Équipe d\'Islande de football|Islande]]')
        pagetext = pagetext.replace('{{ISR football -21}}', '[[Équipe d\'Israël espoirs de football|Israël]]')
        pagetext = pagetext.replace('{{ISR football}}', '[[Équipe d\'Israël de football|Israël]]')
        pagetext = pagetext.replace('{{ISV football}}', '[[Équipe des îles Vierges des États-Unis de football|Îles Vierges des États-Unis]]')
        pagetext = pagetext.replace('{{ITA football -21}}', '[[Équipe d\'Italie espoirs de football|Italie]]')
        pagetext = pagetext.replace('{{ITA football}}', '[[Équipe d\'Italie de football|Italie]]')
        pagetext = pagetext.replace('{{IVB football}}', '[[Équipe des Îles Vierges britanniques de football|Îles Vierges britanniques]]')
        pagetext = pagetext.replace('{{JAM football}}', '[[Équipe de Jamaïque de football|Jamaïque]]')
        pagetext = pagetext.replace('{{JOR football}}', '[[Équipe de Jordanie de football|Jordanie]]')
        pagetext = pagetext.replace('{{JPN football}}', '[[Équipe du Japon de football|Japon]]')
        pagetext = pagetext.replace('{{KAZ football -21}}', '[[Équipe du Kazakhstan espoirs de football|Kazakhstan]]')
        pagetext = pagetext.replace('{{KAZ football}}', '[[Équipe du Kazakhstan de football|Kazakhstan]]')
        pagetext = pagetext.replace('{{KEN football}}', '[[Équipe du Kenya de football|Kenya]]')
        pagetext = pagetext.replace('{{KGZ football}}', '[[Équipe du Kirghizistan de football|Kirghizistan]]')
        pagetext = pagetext.replace('{{KOR football}}', '[[Équipe de Corée du Sud de football|Corée du Sud]]')
        pagetext = pagetext.replace('{{KSA football}}', '[[Équipe d\'Arabie saoudite de football|Arabie saoudite]]')
        pagetext = pagetext.replace('{{KUW football}}', '[[Équipe du Koweït de football|Koweït]]')
        pagetext = pagetext.replace('{{LAO  football}}', '[[Équipe du Laos de football|Laos]]')
        pagetext = pagetext.replace('{{LAT football -21}}', '[[Équipe de Lettonie espoirs de football|Lettonie]]')
        pagetext = pagetext.replace('{{LAT football}}', '[[Équipe de Lettonie de football|Lettonie]]')
        pagetext = pagetext.replace('{{LBA football}}', '[[Équipe de Libye de football|Libye]]')
        pagetext = pagetext.replace('{{LBR football}}', '[[Équipe du Liberia de football|Liberia]]')
        pagetext = pagetext.replace('{{LCA football}}', '[[Équipe de Sainte-Lucie de football|Sainte-Lucie]]')
        pagetext = pagetext.replace('{{LES football}}', '[[Équipe du Lesotho de football|Lesotho]]')
        pagetext = pagetext.replace('{{LIB football}}', '[[Équipe du Liban de football|Liban]]')
        pagetext = pagetext.replace('{{LIE football -21}}', '[[Équipe du Liechtenstein espoirs de football|Liechtenstein]]')
        pagetext = pagetext.replace('{{LIE football}}', '[[Équipe du Liechtenstein de football|Liechtenstein]]')
        pagetext = pagetext.replace('{{LTU football -21}}', '[[Équipe de Lituanie espoirs de football|Lituanie]]')
        pagetext = pagetext.replace('{{LTU football}}', '[[Équipe de Lituanie de football|Lituanie]]')
        pagetext = pagetext.replace('{{LUX football -21}}', '[[Équipe du Luxembourg espoirs de football|Luxembourg]]')
        pagetext = pagetext.replace('{{LUX football}}', '[[Équipe du Luxembourg de football|Luxembourg]]')
        pagetext = pagetext.replace('{{MAC football}}', '[[Équipe de Macao de football|Macao]]')
        pagetext = pagetext.replace('{{MAD football}}', '[[Équipe de Madagascar de football|Madagascar]]')
        pagetext = pagetext.replace('{{MAR football}}', '[[Équipe du Maroc de football|Maroc]]')
        pagetext = pagetext.replace('{{MAS football}}', '[[Équipe de Malaisie de football|Malaisie]]')
        pagetext = pagetext.replace('{{MAW football}}', '[[Équipe du Malawi de football|Malawi]]')
        pagetext = pagetext.replace('{{MDA football -21}}', '[[Équipe de Moldavie espoirs de football|Moldavie]]')
        pagetext = pagetext.replace('{{MDA football}}', '[[Équipe de Moldavie de football|Moldavie]]')
        pagetext = pagetext.replace('{{MDV football}}', '[[Équipe des Maldives de football|Maldives]]')
        pagetext = pagetext.replace('{{MEX football}}', '[[Équipe du Mexique de football|Mexique]]')
        pagetext = pagetext.replace('{{MGL football}}', '[[Équipe de Mongolie de football|Mongolie]]')
        pagetext = pagetext.replace('{{MKD football -21}}', '[[Équipe de Macédoine espoirs de football|Macédoine]]')
        pagetext = pagetext.replace('{{MKD football}}', '[[Équipe de Macédoine de football|Macédoine]]')
        pagetext = pagetext.replace('{{MLI football}}', '[[Équipe du Mali de football|Mali]]')
        pagetext = pagetext.replace('{{MLT football -21}}', '[[Équipe de Malte espoirs de football|Malte]]')
        pagetext = pagetext.replace('{{MLT football}}', '[[Équipe de Malte de football|Malte]]')
        pagetext = pagetext.replace('{{MNE football -21}}', '[[Équipe du Monténégro espoirs de football|Monténégro]]')
        pagetext = pagetext.replace('{{MNE football}}', '[[Équipe du Monténégro de football|Monténégro]]')
        pagetext = pagetext.replace('{{MOZ football}}', '[[Équipe du Mozambique de football|Mozambique]]')
        pagetext = pagetext.replace('{{MRI football}}', '[[Équipe de Maurice de football|Maurice]]')
        pagetext = pagetext.replace('{{MSR football}}', '[[Équipe de Montserrat de football|Montserrat]]')
        pagetext = pagetext.replace('{{MTN football}}', '[[Équipe de Mauritanie de football|Mauritanie]]')
        pagetext = pagetext.replace('{{MYA football}}', '[[Équipe de Birmanie de football|Birmanie]]')
        pagetext = pagetext.replace('{{NAM football}}', '[[Équipe de Namibie de football|Namibie]]')
        pagetext = pagetext.replace('{{NCA football}}', '[[Équipe du Nicaragua de football|Nicaragua]]')
        pagetext = pagetext.replace('{{NCL football}}', '[[Équipe de Nouvelle-Calédonie de football|Nouvelle-Calédonie]]')
        pagetext = pagetext.replace('{{NED football -21}}', '[[Équipe des Pays-Bas espoirs de football|Pays-Bas]]')
        pagetext = pagetext.replace('{{NED football}}', '[[Équipe des Pays-Bas de football|Pays-Bas]]')
        pagetext = pagetext.replace('{{NEP football}}', '[[Équipe du Népal de football|Népal]]')
        pagetext = pagetext.replace('{{NGR football}}', '[[Équipe du Nigeria de football|Nigeria]]')
        pagetext = pagetext.replace('{{NIG football}}', '[[Équipe du Niger de football|Niger]]')
        pagetext = pagetext.replace('{{NIR football -21}}', '[[Équipe d\'Irlande du Nord espoirs de football|Irlande du Nord]]')
        pagetext = pagetext.replace('{{NIR football}}', '[[Équipe d\'Irlande du Nord de football|Irlande du Nord]]')
        pagetext = pagetext.replace('{{NOR football -21}}', '[[Équipe de Norvège espoirs de football|Norvège]]')
        pagetext = pagetext.replace('{{NOR football}}', '[[Équipe de Norvège de football|Norvège]]')
        pagetext = pagetext.replace('{{NZL football}}', '[[Équipe de Nouvelle-Zélande de football|Nouvelle-Zélande]]')
        pagetext = pagetext.replace('{{OMA football}}', '[[Équipe d\'Oman de football|Oman]]')
        pagetext = pagetext.replace('{{PAK football}}', '[[Équipe du Pakistan de football|Pakistan]]')
        pagetext = pagetext.replace('{{PAN football}}', '[[Équipe du Panama de football|Panama]]')
        pagetext = pagetext.replace('{{PAR football}}', '[[Équipe du Paraguay de football|Paraguay]]')
        pagetext = pagetext.replace('{{PER football}}', '[[Équipe du Pérou de football|Pérou]]')
        pagetext = pagetext.replace('{{PHI football}}', '[[Équipe des Philippines de football|Philippines]]')
        pagetext = pagetext.replace('{{PLE football}}', '[[Équipe de Palestine de football|Palestine]]')
        pagetext = pagetext.replace('{{PNG football}}', '[[Équipe de Papouasie-Nouvelle-Guinée de football|Papouasie-Nouvelle-Guinée]]')
        pagetext = pagetext.replace('{{POL football -21}}', '[[Équipe de Pologne espoirs de football|Pologne]]')
        pagetext = pagetext.replace('{{POL football}}', '[[Équipe de Pologne de football|Pologne]]')
        pagetext = pagetext.replace('{{POR football -21}}', '[[Équipe du Portugal espoirs de football|Portugal]]')
        pagetext = pagetext.replace('{{POR football}}', '[[Équipe du Portugal de football|Portugal]]')
        pagetext = pagetext.replace('{{PRK football}}', '[[Équipe de Corée du Nord de football|Corée du Nord]]')
        pagetext = pagetext.replace('{{PUR football}}', '[[Équipe de Porto Rico de football|Porto Rico]]')
        pagetext = pagetext.replace('{{QAT football -21}}', '[[Équipe du Qatar espoirs de football|Qatar]]')
        pagetext = pagetext.replace('{{QAT football}}', '[[Équipe du Qatar de football|Qatar]]')
        pagetext = pagetext.replace('{{ROU football -21}}', '[[Équipe de Roumanie espoirs de football|Roumanie]]')
        pagetext = pagetext.replace('{{ROU football}}', '[[équipe de Roumanie de football|Roumanie]]')
        pagetext = pagetext.replace('{{RSA football}}', '[[Équipe d\'Afrique du Sud de football|Afrique du Sud]]')
        pagetext = pagetext.replace('{{RUS football -21}}', '[[Équipe de Russie espoirs de football|Russie]]')
        pagetext = pagetext.replace('{{RUS football}}', '[[Équipe de Russie de football|Russie]]')
        pagetext = pagetext.replace('{{RWA football}}', '[[Équipe du Rwanda de football|Rwanda]]')
        pagetext = pagetext.replace('{{SAM football}}', '[[Équipe des Samoa de football|Samoa]]')
        pagetext = pagetext.replace('{{SCO football -21}}', '[[Équipe d\'Écosse espoirs de football|Écosse]]')
        pagetext = pagetext.replace('{{SCO football}}', '[[Équipe d\'Écosse de football|Écosse]]')
        pagetext = pagetext.replace('{{SEN football}}', '[[Équipe du Sénégal de football|Sénégal]]')
        pagetext = pagetext.replace('{{SEY football}}', '[[Équipe des Seychelles de football|Seychelles]]')
        pagetext = pagetext.replace('{{SIN football}}', '[[Équipe de Singapour de football|Singapour]]')
        pagetext = pagetext.replace('{{SKN football}}', '[[Équipe de Saint-Christophe-et-Niévès de football|Saint-Christophe-et-Niévès]]')
        pagetext = pagetext.replace('{{SLE football}}', '[[Équipe de Sierra Leone de football|Sierra Leone]]')
        pagetext = pagetext.replace('{{SLO football -21}}', '[[Équipe de Slovénie espoirs de football|France]]')
        pagetext = pagetext.replace('{{SLO football}}', '[[Équipe de Slovénie de football|Slovénie]]')
        pagetext = pagetext.replace('{{SMR football -21}}', '[[Équipe de Saint-Marin espoirs de football|Saint-Marin]]')
        pagetext = pagetext.replace('{{SMR football}}', '[[Équipe de Saint-Marin de football|Saint-Marin]]')
        pagetext = pagetext.replace('{{SOL football}}', '[[Équipe des Salomon de football|Salomon]]')
        pagetext = pagetext.replace('{{SOM football}}', '[[Équipe de Somalie de football|Somalie]]')
        pagetext = pagetext.replace('{{SRB football -21}}', '[[Équipe de Serbie espoirs de football|Serbie]]')
        pagetext = pagetext.replace('{{SRB football}}', '[[Équipe de Serbie de football|Serbie]]')
        pagetext = pagetext.replace('{{SRI football}}', '[[Équipe du Sri Lanka de football|Sri Lanka]]')
        pagetext = pagetext.replace('{{STP football}}', '[[Équipe de Sao Tomé-et-Principe de football|Sao Tomé-et-Principe]]')
        pagetext = pagetext.replace('{{SUD football}}', '[[Équipe du Soudan de football|Soudan]]')
        pagetext = pagetext.replace('{{SUI football -21}}', '[[Équipe de Suisse espoirs de football|Suisse]]')
        pagetext = pagetext.replace('{{SUI football}}', '[[Équipe de Suisse de football|Suisse]]')
        pagetext = pagetext.replace('{{SUR football}}', '[[Équipe du Suriname de football|Suriname]]')
        pagetext = pagetext.replace('{{SVK football -21}}', '[[Équipe de Slovaquie espoirs de football|Slovaquie]]')
        pagetext = pagetext.replace('{{SVK football}}', '[[Équipe de Slovaquie de football|Slovaquie]]')
        pagetext = pagetext.replace('{{SWE football -21}}', '[[Équipe de Suède espoirs de football|Suède]]')
        pagetext = pagetext.replace('{{SWE football}}', '[[Équipe de Suède de football|Suède]]')
        pagetext = pagetext.replace('{{SWZ football}}', '[[Équipe du Swaziland de football|Swaziland]]')
        pagetext = pagetext.replace('{{SYR football -21}}', '[[Équipe de Syrie espoirs de football|Syrie]]')
        pagetext = pagetext.replace('{{SYR football}}', '[[Équipe de Syrie de football|Syrie]]')
        pagetext = pagetext.replace('{{TAH football}}', '[[Équipe de Tahiti de football|Tahiti]]')
        pagetext = pagetext.replace('{{TAN football}}', '[[Équipe de Tanzanie de football|Tanzanie]]')
        pagetext = pagetext.replace('{{TCA football}}', '[[Équipe des îles Turques-et-Caïques de football|Îles Turques-et-Caïques]]')
        pagetext = pagetext.replace('{{TGA football}}', '[[Équipe des Tonga de football|Tonga]]')
        pagetext = pagetext.replace('{{THA football}}', '[[Équipe de Thaïlande de football|Thaïlande]]')
        pagetext = pagetext.replace('{{TJK football}}', '[[Équipe du Tadjikistan de football|Tadjikistan]]')
        pagetext = pagetext.replace('{{TKM football}}', '[[Équipe du Turkménistan de football|Turkménistan]]')
        pagetext = pagetext.replace('{{TLS football}}', '[[Équipe du Timor oriental de football|Timor oriental]]')
        pagetext = pagetext.replace('{{TOG football}}', '[[Équipe du Togo de football|Togo]]')
        pagetext = pagetext.replace('{{TPE football}}', '[[Équipe de Taipei chinois de football|Taïwan]]')
        pagetext = pagetext.replace('{{TRI football}}', '[[Équipe de Trinité-et-Tobago de football|Trinité-et-Tobago]]')
        pagetext = pagetext.replace('{{TUN football -21}}', '[[Équipe de Tunisie olympique de football|Tunisie]]')
        pagetext = pagetext.replace('{{TUN football}}', '[[Équipe de Tunisie de football|Tunisie]]')
        pagetext = pagetext.replace('{{TUR football -21}}', '[[Équipe de Turquie espoirs de football|Turquie]]')
        pagetext = pagetext.replace('{{TUR football}}', '[[Équipe de Turquie de football|Turquie]]')
        pagetext = pagetext.replace('{{UAE football -21}}', '[[Équipe des Émirats Arabes Unis espoirs de football|Émirats Arabes Unis]]')
        pagetext = pagetext.replace('{{UAE football}}', '[[Équipe des Émirats arabes unis de football|Émirats arabes unis]]')
        pagetext = pagetext.replace('{{UGA football}}', '[[Équipe d\'Ouganda de football|Ouganda]]')
        pagetext = pagetext.replace('{{UKR football -21}}', '[[Équipe d\'Ukraine espoirs de football|Ukraine]]')
        pagetext = pagetext.replace('{{UKR football}}', '[[Équipe d\'Ukraine de football|Ukraine]]')
        pagetext = pagetext.replace('{{URU football}}', '[[Équipe d\'Uruguay de football|Uruguay]]')
        pagetext = pagetext.replace('{{USA football}}', '[[Équipe des États-Unis de soccer|États-Unis]]')
        pagetext = pagetext.replace('{{UZB football}}', '[[Équipe d\'Ouzbékistan de football|Ouzbékistan]]')
        pagetext = pagetext.replace('{{VAN football}}', '[[Équipe du Vanuatu de football|Vanuatu]]')
        pagetext = pagetext.replace('{{VEN football}}', '[[Équipe du Venezuela de football|Venezuela]]')
        pagetext = pagetext.replace('{{VIE football}}', '[[Équipe du Viêt Nam de football|Viêt Nam]]')
        pagetext = pagetext.replace('{{VIN football}}', '[[Équipe de Saint-Vincent-et-les-Grenadines de football|Saint-Vincent-et-les-Grenadines]]')
        pagetext = pagetext.replace('{{WAL football -21}}', '[[Équipe du pays de Galles espoirs de football|Pays de Galles]]')
        pagetext = pagetext.replace('{{WAL football}}', '[[Équipe du pays de Galles de football|Pays de Galles]]')
        pagetext = pagetext.replace('{{YEM football}}', '[[Équipe du Yémen de football|Yémen]]')
        pagetext = pagetext.replace('{{ZAM  football}}', '[[Équipe de Zambie de football|Zambie]]')
        pagetext = pagetext.replace('{{ZIM football}}', '[[Équipe du Zimbabwe de football|Zimbabwe]]')

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
                
        pagetext = page.get()
        # on met de côté les tableaux entraîneur et junior
        pagetext = re.sub(r'carrière entraîneur *= *{{', 'carrière entraîneur = {{Pouet', pagetext)
        pagetext = re.sub(r'parcours junior *= *{{', 'parcours junior = {{Pouet', pagetext)
        if self.param_amateur is not True:
            pagetext = re.sub(r'parcours amateur *= *{{', 'parcours amateur = {{Pouet', pagetext)

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
                            % (field, value, int(field) % 3))
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
                            #if re.search('',value)
                            value=self.nettoyage_selections(value)
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
                        #qualif = qualif.replace ('{{Clr}}', '')
                        #qualif = qualif.replace ('{{Year|', '')
                        #qualif = qualif.replace ('{{prêt}}', '')
                        qualif = re.sub(r'{{0(\|0+)?}}', '', qualif)
                        qualif = re.sub(r'[a-zA-Zéêû&; \.\[\?\]\{\}\|]', '', qualif)
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
    template_title = u'Trois colonnes'

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen = pg.GeneratorFactory()

    param_debug = False
    param_amateur = False
    param_first = None
    
    for arg in local_args:
        if arg == '-d':
            param_debug = True
        elif arg == '-am':
            param_amateur = True
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

    bot = HarvestRobot(generator, template_title, fields, param_first, param_debug, param_amateur)
    bot.run()

if __name__ == "__main__":
    main()
