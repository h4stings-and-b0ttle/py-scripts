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

        pagetext = pagetext.replace('{{ABK football}}', '[[Équipe d\'Abkhazie de football|Abkhazie]]')
        pagetext = pagetext.replace('{{ACO football}}', '[[Équipe des Açores de football|Açores]]')
        pagetext = pagetext.replace('{{ADU football}}', '[[Équipe d\'Andalousie de football|Andalousie]]')
        pagetext = pagetext.replace('{{AFG football (1930-1973)}}', '[[Équipe d\'Afghanistan de football|Afghanistan]]')
        pagetext = pagetext.replace('{{AFG football (1974-1978)}}', '[[Équipe d\'Afghanistan de football|Afghanistan]]')
        pagetext = pagetext.replace('{{AFG football (1978-1980)}}', '[[Équipe d\'Afghanistan de football|Afghanistan]]')
        pagetext = pagetext.replace('{{AFG football (1980-1987)}}', '[[Équipe d\'Afghanistan de football|Afghanistan]]')
        pagetext = pagetext.replace('{{AFG football (2002-2004)}}', '[[Équipe d\'Afghanistan de football|Afghanistan]]')
        pagetext = pagetext.replace('{{AFG football}}', '[[Équipe d\'Afghanistan de football|Afghanistan]]')
        pagetext = pagetext.replace('{{AHO football (1921-1959)}}', '[[Équipe des Antilles néerlandaises de football|Antilles néerlandaises]]')
        pagetext = pagetext.replace('{{AHO football (1959-1986)}}', '[[Équipe des Antilles néerlandaises de football|Antilles néerlandaises]]')
        pagetext = pagetext.replace('{{AHO football}}', '[[Équipe des Antilles néerlandaises de football|Antilles néerlandaises]]')
        pagetext = pagetext.replace('{{AIA football}}', '[[Équipe d\'Anguilla de football|Anguilla]]')
        pagetext = pagetext.replace('{{ALA football}}', '[[Équipe d\'Åland de football|Åland]]')
        pagetext = pagetext.replace('{{ALB football (1934-1939)}}', '[[Équipe d\'Albanie de football|Albanie]]')
        pagetext = pagetext.replace('{{ALB football (1946-1991)}}', '[[Équipe d\'Albanie de football|Albanie]]')
        pagetext = pagetext.replace('{{ALB football -21}}', '[[Équipe d\'Albanie espoirs de football|Albanie]]')
        pagetext = pagetext.replace('{{ALB football}}', '[[Équipe d\'Albanie de football|Albanie]]')
        pagetext = pagetext.replace('{{ALD football}}', '[[Équipe d\'Aurigny de football|Aurigny]]')
        pagetext = pagetext.replace('{{ALG football -21}}', '[[Équipe d\'Algérie espoirs de football|Algérie]]')
        pagetext = pagetext.replace('{{ALG football A\'}}', '[[Équipe d\'Algérie de football A\'|Algérie A\']]')
        pagetext = pagetext.replace('{{ALG football}}', '[[Équipe d\'Algérie de football|Algérie]]')
        pagetext = pagetext.replace('{{AND football -21}}', '[[Équipe d\'Andorre espoirs de football|Andorre]]')
        pagetext = pagetext.replace('{{AND football}}', '[[Équipe d\'Andorre de football|Andorre]]')
        pagetext = pagetext.replace('{{ANG football}}', '[[Équipe d\'Angola de football|Angola]]')
        pagetext = pagetext.replace('{{ANT football}}', '[[Équipe d\'Antigua-et-Barbuda de football|Antigua-et-Barbuda]]')
        pagetext = pagetext.replace('{{ARA football}}', '[[Équipe d\'Aragon de football|Aragon]]')
        pagetext = pagetext.replace('{{ARG football -17}}', '[[Équipe d\'Argentine de football des moins de 17 ans|Argentine]]')
        pagetext = pagetext.replace('{{ARG football -21}}', '[[Équipe d\'Argentine espoirs de football|Argentine]]')
        pagetext = pagetext.replace('{{ARG football}}', '[[Équipe d\'Argentine de football|Argentine]]')
        pagetext = pagetext.replace('{{ARM football -21}}', '[[Équipe d\'Arménie espoirs de football|Arménie]]')
        pagetext = pagetext.replace('{{ARM football}}', '[[Équipe d\'Arménie de football|Arménie]]')
        pagetext = pagetext.replace('{{ARU football}}', '[[Équipe d\'Aruba de football|Aruba]]')
        pagetext = pagetext.replace('{{ASA football}}', '[[Équipe des Samoa américaines de football|Samoa américaines]]')
        pagetext = pagetext.replace('{{AUS football -17}}', '[[Équipe d\'Australie de football des moins de 17 ans|Australie]]')
        pagetext = pagetext.replace('{{AUS football -21}}', '[[Équipe d\'Australie espoirs de football|Australie]]')
        pagetext = pagetext.replace('{{AUS football}}', '[[Équipe d\'Australie de football|Australie]]')
        pagetext = pagetext.replace('{{AUT football (1804)}}', '[[Équipe d\'Autriche de football|Autriche]]')
        pagetext = pagetext.replace('{{AUT football (1867-1918)}}', '[[Équipe d\'Autriche de football|Autriche]]')
        pagetext = pagetext.replace('{{AUT football -21}}', '[[Équipe d\'Autriche espoirs de football|Autriche]]')
        pagetext = pagetext.replace('{{AUT football}}', '[[Équipe d\'Autriche de football|Autriche]]')
        pagetext = pagetext.replace('{{AZE football -21}}', '[[Équipe d\'Azerbaïdjan espoirs de football|Azerbaïdjan]]')
        pagetext = pagetext.replace('{{AZE football}}', '[[Équipe d\'Azerbaïdjan de football|Azerbaïdjan]]')
        pagetext = pagetext.replace('{{BAH football}}', '[[Équipe des Bahamas de football|Bahamas]]')
        pagetext = pagetext.replace('{{BAN football}}', '[[Équipe du Bangladesh de football|Bangladesh]]')
        pagetext = pagetext.replace('{{BAR football}}', '[[Équipe de la Barbade de football|Barbade]]')
        pagetext = pagetext.replace('{{BDI football (1967-1982)}}', '[[Équipe du Burundi de football|Burundi]]')
        pagetext = pagetext.replace('{{BDI football}}', '[[Équipe du Burundi de football|Burundi]]')
        pagetext = pagetext.replace('{{BEL football -17}}', '[[Équipe de Belgique de football des moins de 17 ans|Belgique]]')
        pagetext = pagetext.replace('{{BEL football espoirs}}', '[[Équipe de Belgique espoirs de football|Belgique]]')
        pagetext = pagetext.replace('{{BEL football}}', '[[Équipe de Belgique de football|Belgique]]')
        pagetext = pagetext.replace('{{BEN football (1975-1990)}}', '[[Équipe du Bénin de football|Bénin]]')
        pagetext = pagetext.replace('{{BEN football}}', '[[Équipe du Bénin de football|Bénin]]')
        pagetext = pagetext.replace('{{BER football}}', '[[Équipe des Bermudes de football|Bermudes]]')
        pagetext = pagetext.replace('{{BHU football}}', '[[Équipe du Bhoutan de football|Bhoutan]]')
        pagetext = pagetext.replace('{{BIH football (1992-1998)}}', '[[Équipe de Bosnie-Herzégovine de football|Bosnie-Herzégovine]]')
        pagetext = pagetext.replace('{{BIH football -21}}', '[[Équipe de Bosnie-Herzégovine espoirs de football|Bosnie-Herzégovine]]')
        pagetext = pagetext.replace('{{BIH football}}', '[[Équipe de Bosnie-Herzégovine de football|Bosnie-Herzégovine]]')
        pagetext = pagetext.replace('{{BIZ football}}', '[[Équipe du Belize de football|Belize]]')
        pagetext = pagetext.replace('{{BLR football (1991-1995)}}', '[[Équipe de Biélorussie de football|Biélorussie]]')
        pagetext = pagetext.replace('{{BLR football (1995-2012)}}', '[[Équipe de Biélorussie de football|Biélorussie]]')
        pagetext = pagetext.replace('{{BLR football -21}}', '[[Équipe de Biélorussie espoirs de football|Biélorussie]]')
        pagetext = pagetext.replace('{{BLR football}}', '[[Équipe de Biélorussie de football|Biélorussie]]')
        pagetext = pagetext.replace('{{BOL football -17}}', '[[Équipe de Bolivie de football des moins de 17 ans|Bolivie]]')
        pagetext = pagetext.replace('{{BOL football}}', '[[Équipe de Bolivie de football|Bolivie]]')
        pagetext = pagetext.replace('{{BON football}}', '[[Équipe de Bonaire de football|Bonaire]]')
        pagetext = pagetext.replace('{{BOT football}}', '[[Équipe du Botswana de football|Botswana]]')
        pagetext = pagetext.replace('{{BRA football (1889-1960)}}', '[[Équipe du Brésil de football|Brésil]]')
        pagetext = pagetext.replace('{{BRA football (1960-1968)}}', '[[Équipe du Brésil de football|Brésil]]')
        pagetext = pagetext.replace('{{BRA football (1968-1992)}}', '[[Équipe du Brésil de football|Brésil]]')
        pagetext = pagetext.replace('{{BRA football -17}}', '[[Équipe du Brésil de football des moins de 17 ans|Brésil]]')
        pagetext = pagetext.replace('{{BRA football}}', '[[Équipe du Brésil de football|Brésil]]')
        pagetext = pagetext.replace('{{BRN football (1932-1972)}}', '[[Équipe de Bahreïn de football|Bahreïn]]')
        pagetext = pagetext.replace('{{BRN football (1972-2002)}}', '[[Équipe de Bahreïn de football|Bahreïn]]')
        pagetext = pagetext.replace('{{BRN football}}', '[[Équipe de Bahreïn de football|Bahreïn]]')
        pagetext = pagetext.replace('{{BRU football}}', '[[Équipe de Brunei de football|Brunei]]')
        pagetext = pagetext.replace('{{BUL football (1946-1948)}}', '[[Équipe de Bulgarie de football|Bulgarie]]')
        pagetext = pagetext.replace('{{BUL football (1948-1967)}}', '[[Équipe de Bulgarie de football|Bulgarie]]')
        pagetext = pagetext.replace('{{BUL football (1967-1971)}}', '[[Équipe de Bulgarie de football|Bulgarie]]')
        pagetext = pagetext.replace('{{BUL football (1971-1990)}}', '[[Équipe de Bulgarie de football|Bulgarie]]')
        pagetext = pagetext.replace('{{BUL football -21}}', '[[Équipe de Bulgarie espoirs de football|Bulgarie]]')
        pagetext = pagetext.replace('{{BUL football}}', '[[Équipe de Bulgarie de football|Bulgarie]]')
        pagetext = pagetext.replace('{{BUR football -20}}', '[[Équipe du Burkina Faso de football des moins de 20 ans|Burkina Faso]]')
        pagetext = pagetext.replace('{{BUR football}}', '[[Équipe du Burkina Faso de football|Burkina Faso]]')
        pagetext = pagetext.replace('{{BZH football}}', '[[Équipe de Bretagne de football|Bretagne]]')
        pagetext = pagetext.replace('{{CAF football}}', '[[Équipe de République centrafricaine de football|République centrafricaine]]')
        pagetext = pagetext.replace('{{CAL football}}', '[[Équipe de Castille et León de football|Castille et León]]')
        pagetext = pagetext.replace('{{CAM football (1970-1975)}}', '[[Équipe du Cambodge de football|Cambodge]]')
        pagetext = pagetext.replace('{{CAM football}}', '[[Équipe du Cambodge de football|Cambodge]]')
        pagetext = pagetext.replace('{{CAN football (1921-1957)}}', '[[Équipe du Canada de soccer|Canada]]')
        pagetext = pagetext.replace('{{CAN football (1957-1964)}}', '[[Équipe du Canada de soccer|Canada]]')
        pagetext = pagetext.replace('{{CAN football -17}}', '[[Équipe du Canada de soccer des moins de 17 ans|Canada]]')
        pagetext = pagetext.replace('{{CAN football -20}}', '[[Équipe du Canada de football des moins de 20 ans|Canada]]')
        pagetext = pagetext.replace('{{CAN football}}', '[[Équipe du Canada de soccer|Canada]]')
        pagetext = pagetext.replace('{{CAS football}}', '[[Équipe des Canaries de football|Canaries]]')
        pagetext = pagetext.replace('{{CAT football}}', '[[Équipe de Catalogne de football|Catalogne]]')
        pagetext = pagetext.replace('{{CAY football (1958-1999)}}', '[[Équipe des îles Caïmans de football|Îles Caïmans]]')
        pagetext = pagetext.replace('{{CAY football}}', '[[Équipe des îles Caïmans de football|Îles Caïmans]]')
        pagetext = pagetext.replace('{{CEI football}}', '[[Équipe de la communauté des États indépendants de football|CEI]]')
        pagetext = pagetext.replace('{{CGO football (1970-1991)}}', '[[Équipe du Congo de football|Congo]]')
        pagetext = pagetext.replace('{{CGO football -17}}', '[[Équipe du Congo de football des moins de 17 ans|Congo]]')
        pagetext = pagetext.replace('{{CGO football -20}}', '[[Équipe de France du Congo des moins de 20 ans|Congo]]')
        pagetext = pagetext.replace('{{CGO football}}', '[[Équipe du Congo de football|Congo]]')
        pagetext = pagetext.replace('{{CHA football}}', '[[Équipe du Tchad de football|Tchad]]')
        pagetext = pagetext.replace('{{CHI football -21}}', '[[Équipe du Chili espoirs de football|Chili]]')
        pagetext = pagetext.replace('{{CHI football}}', '[[Équipe du Chili de football|Chili]]')
        pagetext = pagetext.replace('{{CHN football (1912-1928)}}', '[[Équipe de Chine de football|Chine]]')
        pagetext = pagetext.replace('{{CHN football (1928-1949)}}', '[[Équipe de Chine de football|Chine]]')
        pagetext = pagetext.replace('{{CHN football -17}}', '[[Équipe de Chine de football des moins de 17 ans|Chine]]')
        pagetext = pagetext.replace('{{CHN football -21}}', '[[Équipe de Chine espoirs de football|Chine]]')
        pagetext = pagetext.replace('{{CHN football}}', '[[Équipe de Chine de football|Chine]]')
        pagetext = pagetext.replace('{{CIV football -17}}', '[[Équipe de Côte d\'Ivoire de football des moins de 17 ans|Côte d\'Ivoire]]')
        pagetext = pagetext.replace('{{CIV football -20}}', '[[Équipe de la Côte d\'Ivoire de football des moins de 20 ans|Côte d\'Ivoire]]')
        pagetext = pagetext.replace('{{CIV football}}', '[[Équipe de Côte d\'Ivoire de football|Côte d’Ivoire]]')
        pagetext = pagetext.replace('{{CMR football (1957-1961)}}', '[[Équipe du Cameroun de football|Cameroun]]')
        pagetext = pagetext.replace('{{CMR football (1961-1975)}}', '[[Équipe du Cameroun de football|Cameroun]]')
        pagetext = pagetext.replace('{{CMR football -20}}', '[[Équipe du Cameroun de football des moins de 20 ans|Cameroun]]')
        pagetext = pagetext.replace('{{CMR football}}', '[[Équipe du Cameroun de football|Cameroun]]')
        pagetext = pagetext.replace('{{COD football (1908-1960)}}', '[[Équipe de République démocratique du Congo de football|Congo belge]]')
        pagetext = pagetext.replace('{{COD football (1960-1963)}}', '[[Équipe de République démocratique du Congo de football|Congo Léopoldville]]')
        pagetext = pagetext.replace('{{COD football (1963-1966)}}', '[[Équipe de République démocratique du Congo de football|Congo Léopoldville]]')
        pagetext = pagetext.replace('{{COD football (1966-1971)}}', '[[Équipe de République démocratique du Congo de football|Congo Kinshasa]]')
        pagetext = pagetext.replace('{{COD football (1997-2003)}}', '[[Équipe de République démocratique du Congo de football|Rép. dém. du Congo]]')
        pagetext = pagetext.replace('{{COD football (2003-2006)}}', '[[Équipe de République démocratique du Congo de football|Rép. dém. du Congo]]')
        pagetext = pagetext.replace('{{COD football}}', '[[Équipe de République démocratique du Congo de football|Rép. dém. du Congo]]')
        pagetext = pagetext.replace('{{COK football}}', '[[Équipe des îles Cook de football|Îles Cook]]')
        pagetext = pagetext.replace('{{COL football}}', '[[Équipe de Colombie de football|Colombie]]')
        pagetext = pagetext.replace('{{COM football (1978-1992)}}', '[[Équipe des Comores de football|Comores]]')
        pagetext = pagetext.replace('{{COM football (1992-1996)}}', '[[Équipe des Comores de football|Comores]]')
        pagetext = pagetext.replace('{{COM football (1996-2001)}}', '[[Équipe des Comores de football|Comores]]')
        pagetext = pagetext.replace('{{COM football}}', '[[Équipe des Comores de football|Comores]]')
        pagetext = pagetext.replace('{{COR football}}', '[[Équipe de Corse de football|Corse]]')
        pagetext = pagetext.replace('{{CPV football (1975-1992)}}', '[[Équipe du Cap-Vert de football|Cap-Vert]]')
        pagetext = pagetext.replace('{{CPV football}}', '[[Équipe du Cap-Vert de football|Cap-Vert]]')
        pagetext = pagetext.replace('{{CRC football -17}}', '[[Équipe du Costa Rica de football des moins de 17 ans|Costa Rica]]')
        pagetext = pagetext.replace('{{CRC football}}', '[[Équipe du Costa Rica de football|Costa Rica]]')
        pagetext = pagetext.replace('{{CRO football (1939-1941)}}', '[[Équipe de Croatie de football|Croatie]]')
        pagetext = pagetext.replace('{{CRO football (1941-1943)}}', '[[Équipe de Croatie de football|Croatie]]')
        pagetext = pagetext.replace('{{CRO football (1943-1945)}}', '[[Équipe de Croatie de football|Croatie]]')
        pagetext = pagetext.replace('{{CRO football -21}}', '[[Équipe de Croatie espoirs de football|Croatie]]')
        pagetext = pagetext.replace('{{CRO football}}', '[[Équipe de Croatie de football|Croatie]]')
        pagetext = pagetext.replace('{{CTB football}}', '[[Équipe de Cantabrie de football|Cantabrie]]')
        pagetext = pagetext.replace('{{CUB football}}', '[[Équipe de Cuba de football|Cuba]]')
        pagetext = pagetext.replace('{{CUR football}}', '[[Équipe de Curaçao de football|Curaçao]]')
        pagetext = pagetext.replace('{{CYP football -21}}', '[[Équipe de Chypre espoirs de football|Chypre]]')
        pagetext = pagetext.replace('{{CYP football}}', '[[Équipe de Chypre de football|Chypre]]')
        pagetext = pagetext.replace('{{CZE football -21}}', '[[Équipe de République tchèque espoirs de football|République tchèque]]')
        pagetext = pagetext.replace('{{CZE football}}', '[[Équipe de République tchèque de football|République tchèque]]')
        pagetext = pagetext.replace('{{DAH football}}', '[[Équipe du Bénin de football|Dahomey]]')
        pagetext = pagetext.replace('{{DEN football -17}}', '[[Équipe du Danemark de football des moins de 17 ans|Danemark]]')
        pagetext = pagetext.replace('{{DEN football -21}}', '[[Équipe du Danemark espoirs de football|Danemark]]')
        pagetext = pagetext.replace('{{DEN football}}', '[[Équipe du Danemark de football|Danemark]]')
        pagetext = pagetext.replace('{{DJI football}}', '[[Équipe de Djibouti de football|Djibouti]]')
        pagetext = pagetext.replace('{{DMA football}}', '[[Équipe de Dominique de football|Dominique]]')
        pagetext = pagetext.replace('{{DOM football}}', '[[Équipe de République dominicaine de football|République dominicaine]]')
        pagetext = pagetext.replace('{{ECU football -17}}', '[[Équipe d\'Équateur de football des moins de 17 ans|Équateur]]')
        pagetext = pagetext.replace('{{ECU football}}', '[[Équipe d\'Équateur de football|Équateur]]')
        pagetext = pagetext.replace('{{EGY football (1881-1922)}}', '[[Équipe d\'Égypte de football|Égypte]]')
        pagetext = pagetext.replace('{{EGY football (1922-1952)}}', '[[Équipe d\'Égypte de football|Égypte]]')
        pagetext = pagetext.replace('{{EGY football (1952-1958)}}', '[[Équipe d\'Égypte de football|Égypte]]')
        pagetext = pagetext.replace('{{EGY football (1972-1984)}}', '[[Équipe d\'Égypte de football|Égypte]]')
        pagetext = pagetext.replace('{{EGY football -17}}', '[[Équipe d\'Égypte de football des moins de 17 ans|Égypte]]')
        pagetext = pagetext.replace('{{EGY football -20}}', '[[Équipe d\'Egypte de football des moins de 20 ans|Egypte]]')
        pagetext = pagetext.replace('{{EGY football -21}}', '[[Équipe d\'Égypte espoirs de football|Égypte]]')
        pagetext = pagetext.replace('{{EGY football}}', '[[Équipe d\'Égypte de football|Égypte]]')
        pagetext = pagetext.replace('{{EIR football}}', '[[Équipe d\'Irlande de football|Irlande]]')
        pagetext = pagetext.replace('{{ENG football -17}}', '[[Équipe d\'Angleterre de football des moins de 17 ans|Angleterre]]')
        pagetext = pagetext.replace('{{ENG football -21}}', '[[Équipe d\'Angleterre espoirs de football|Angleterre]]')
        pagetext = pagetext.replace('{{ENG football amateur}}', '[[Équipe d\'Angleterre de football amateur|Angleterre amateur]]')
        pagetext = pagetext.replace('{{ENG football}}', '[[Équipe d\'Angleterre de football|Angleterre]]')
        pagetext = pagetext.replace('{{ERI football}}', '[[Équipe d\'Érythrée de football|Érythrée]]')
        pagetext = pagetext.replace('{{ESA football}}', '[[Équipe du Salvador de football|Salvador]]')
        pagetext = pagetext.replace('{{ESP football (1875-1931)}}', '[[Équipe d\'Espagne de football|Espagne]]')
        pagetext = pagetext.replace('{{ESP football (1931-1939)}}', '[[Équipe d\'Espagne de football|Espagne]]')
        pagetext = pagetext.replace('{{ESP football (1939-1945)}}', '[[Équipe d\'Espagne de football|Espagne]]')
        pagetext = pagetext.replace('{{ESP football (1945-1977)}}', '[[Équipe d\'Espagne de football|Espagne]]')
        pagetext = pagetext.replace('{{ESP football (1977-1981)}}', '[[Équipe d\'Espagne de football|Espagne]]')
        pagetext = pagetext.replace('{{ESP football -21}}', '[[Équipe d\'Espagne espoirs de football|Espagne]]')
        pagetext = pagetext.replace('{{ESP football}}', '[[Équipe d\'Espagne de football|Espagne]]')
        pagetext = pagetext.replace('{{EST football -21}}', '[[Équipe d\'Estonie espoirs de football|Estonie]]')
        pagetext = pagetext.replace('{{EST football}}', '[[Équipe d\'Estonie de football|Estonie]]')
        pagetext = pagetext.replace('{{ETH football (1941-1974)}}', '[[Équipe d\'Éthiopie de football|Éthiopie]]')
        pagetext = pagetext.replace('{{ETH football (1974-1975)}}', '[[Équipe d\'Éthiopie de football|Éthiopie]]')
        pagetext = pagetext.replace('{{ETH football (1975-1987)}}', '[[Équipe d\'Éthiopie de football|Éthiopie]]')
        pagetext = pagetext.replace('{{ETH football (1987-1991)}}', '[[Équipe d\'Éthiopie de football|Éthiopie]]')
        pagetext = pagetext.replace('{{ETH football (1991-1996)}}', '[[Équipe d\'Éthiopie de football|Éthiopie]]')
        pagetext = pagetext.replace('{{ETH football}}', '[[Équipe d\'Éthiopie de football|Éthiopie]]')
        pagetext = pagetext.replace('{{EUK football}}', '[[Équipe du Pays basque de football|Pays basque]]')
        pagetext = pagetext.replace('{{FIJ football (1924-1970)}}', '[[Équipe de Fidji de football|Fidji]]')
        pagetext = pagetext.replace('{{FIJ football}}', '[[Équipe des Fidji de football|Fidji]]')
        pagetext = pagetext.replace('{{FIN football -21}}', '[[Équipe de Finlande espoirs de football|Finlande]]')
        pagetext = pagetext.replace('{{FIN football}}', '[[Équipe de Finlande de football|Finlande]]')
        pagetext = pagetext.replace('{{FLN football}}', '[[Équipe du Front de libération nationale algérien de football|FLN]]')
        pagetext = pagetext.replace('{{FRA football -17}}', '[[Équipe de France de football des moins de 17 ans|France]]')
        pagetext = pagetext.replace('{{FRA football -20}}', '[[Équipe de France de football des moins de 20 ans|France]]')
        pagetext = pagetext.replace('{{FRA football -21}}', '[[Équipe de France espoirs de football|France]]')
        pagetext = pagetext.replace('{{FRA football}}', '[[Équipe de France de football|France]]')
        pagetext = pagetext.replace('{{FRG football -17}}', '[[Équipe d\'Allemagne de football des moins de 17 ans|Allemagne de l\'Ouest]]')
        pagetext = pagetext.replace('{{FRG football}}', '[[Équipe d\'Allemagne de football|Allemagne de l’Ouest]]')
        pagetext = pagetext.replace('{{FRO football -21}}', '[[Équipe des Îles Féroé espoirs de football|Îles Féroé]]')
        pagetext = pagetext.replace('{{FRO football}}', '[[Équipe des îles Féroé de football|Îles Féroé]]')
        pagetext = pagetext.replace('{{FSM football}}', '[[Équipe de Micronésie de football|Micronésie]]')
        pagetext = pagetext.replace('{{FYA football}}', '[[Équipe de Frøya de football|Frøya]]')
        pagetext = pagetext.replace('{{GAB football -20}}', '[[Équipe du Gabon de football des moins de 20 ans|Gabon]]')
        pagetext = pagetext.replace('{{GAB football}}', '[[Équipe du Gabon de football|Gabon]]')
        pagetext = pagetext.replace('{{GAL football}}', '[[Équipe de Galice de football|Galice]]')
        pagetext = pagetext.replace('{{GAM football}}', '[[Équipe de Gambie de football|Gambie]]')
        pagetext = pagetext.replace('{{GBR football}}', '[[Équipe de Grande-Bretagne olympique de football|Grande-Bretagne]]')
        pagetext = pagetext.replace('{{GBS football}}', '[[Équipe de Guinée-Bissau de football|Guinée-Bissau]]')
        pagetext = pagetext.replace('{{GDR football (1949-1959)}}', '[[Équipe d\'Allemagne de l\'Est de football|Allemagne de l\'Est]]')
        pagetext = pagetext.replace('{{GDR football}}', '[[Équipe d\'Allemagne de l\'Est de football|Allemagne de l\'Est]]')
        pagetext = pagetext.replace('{{GEO football (1990-2004)}}', '[[Équipe de Géorgie de football|Géorgie]]')
        pagetext = pagetext.replace('{{GEO football -17}}', '[[Équipe de Géorgie de football des moins de 17 ans|Géorgie]]')
        pagetext = pagetext.replace('{{GEO football -21}}', '[[Équipe de Géorgie espoirs de football|Géorgie]]')
        pagetext = pagetext.replace('{{GEO football}}', '[[Équipe de Géorgie de football|Géorgie]]')
        pagetext = pagetext.replace('{{GEQ football}}', '[[Équipe de Guinée équatoriale de football|Guinée équatoriale]]')
        pagetext = pagetext.replace('{{GER football (1871-1918)}}', '[[Équipe d\'Allemagne de football|Allemagne]]')
        pagetext = pagetext.replace('{{GER football (1919-1933)}}', '[[Équipe d\'Allemagne de football|Allemagne]]')
        pagetext = pagetext.replace('{{GER football (1933-1935)}}', '[[Équipe d\'Allemagne de football|Allemagne]]')
        pagetext = pagetext.replace('{{GER football (1933-1945)}}', '[[Équipe d\'Allemagne de football|Allemagne]]')
        pagetext = pagetext.replace('{{GER football (1946-1949)}}', '[[Équipe d\'Allemagne de football|Allemagne]]')
        pagetext = pagetext.replace('{{GER football -17}}', '[[Équipe d\'Allemagne de football des moins de 17 ans|Allemagne]]')
        pagetext = pagetext.replace('{{GER football -21}}', '[[Équipe d\'Allemagne espoirs de football|Allemagne]]')
        pagetext = pagetext.replace('{{GER football}}', '[[Équipe d\'Allemagne de football|Allemagne]]')
        pagetext = pagetext.replace('{{GHA football -17}}', '[[Équipe du Ghana de football des moins de 17 ans|Ghana -17 ans]]')
        pagetext = pagetext.replace('{{GHA football -20}}', '[[Équipe du Ghana de football des moins de 20 ans|Ghana]]')
        pagetext = pagetext.replace('{{GHA football}}', '[[Équipe du Ghana de football|Ghana]]')
        pagetext = pagetext.replace('{{GIB football}}', '[[Équipe de Gibraltar de football|Gibraltar]]')
        pagetext = pagetext.replace('{{GLP football}}', '[[Équipe de Guadeloupe de football|Guadeloupe]]')
        pagetext = pagetext.replace('{{GOC football}}', '[[Équipe du Ghana de football|Côte-de-l\'Or]]')
        pagetext = pagetext.replace('{{GRE football (1828-1969; 1975-1978)}}', '[[Équipe de Grèce de football|Grèce]]')
        pagetext = pagetext.replace('{{GRE football (1970-1975)}}', '[[Équipe de Grèce de football|Grèce]]')
        pagetext = pagetext.replace('{{GRE football -21}}', '[[Équipe de Grèce espoirs de football|Grèce]]')
        pagetext = pagetext.replace('{{GRE football}}', '[[Équipe de Grèce de football|Grèce]]')
        pagetext = pagetext.replace('{{GRL football}}', '[[Équipe du Groenland de football|Groenland]]')
        pagetext = pagetext.replace('{{GRN football}}', '[[Équipe de Grenade de football|Grenade]]')
        pagetext = pagetext.replace('{{GUA football}}', '[[Équipe du Guatemala de football|Guatemala]]')
        pagetext = pagetext.replace('{{GUE football}}', '[[Équipe de Guernesey de football|Guernesey]]')
        pagetext = pagetext.replace('{{GUF football}}', '[[Équipe de Guyane de football|Guyane]]')
        pagetext = pagetext.replace('{{GUI football -17}}', '[[Équipe de Guinée de football des moins de 17 ans|Guinée]]')
        pagetext = pagetext.replace('{{GUI football}}', '[[Équipe de Guinée de football|Guinée]]')
        pagetext = pagetext.replace('{{GUM football}}', '[[Équipe de Guam de football|Guam]]')
        pagetext = pagetext.replace('{{GUY football (1919-1954)}}', '[[Équipe du Guyana de football|Guyane britannique]]')
        pagetext = pagetext.replace('{{GUY football (1954-1966)}}', '[[Équipe du Guyana de football|Guyane britannique]]')
        pagetext = pagetext.replace('{{GUY football}}', '[[Équipe du Guyana de football|Guyana]]')
        pagetext = pagetext.replace('{{GXZ football}}', '[[Équipe du Guangxi de football|Guangxi]]')
        pagetext = pagetext.replace('{{HAI (1964-1986) football}}', '[[Équipe d\'Haïti de football|Haïti]]')
        pagetext = pagetext.replace('{{HAI football (1964-1986)}}', '[[Équipe d\'Haïti de football|Haïti]]')
        pagetext = pagetext.replace('{{HAI football -20}}', '[[Équipe de Haïti de football des moins de 20 ans|Haïti]]')
        pagetext = pagetext.replace('{{HAI football}}', '[[Équipe d\'Haïti de football|Haïti]]')
        pagetext = pagetext.replace('{{HEB football}}', '[[Équipe du Vanuatu de football|Nouvelles-Hébrides]]')
        pagetext = pagetext.replace('{{HKG football (1910-1959)}}', '[[Équipe de Hong Kong de football|Hong Kong]]')
        pagetext = pagetext.replace('{{HKG football (1959-1997)}}', '[[Équipe de Hong Kong de football|Hong Kong]]')
        pagetext = pagetext.replace('{{HKG football}}', '[[Équipe de Hong Kong de football|Hong Kong]]')
        pagetext = pagetext.replace('{{HON football}}', '[[Équipe du Honduras de football|Honduras]]')
        pagetext = pagetext.replace('{{HUN football (1867-1918)}}', '[[Équipe de Hongrie de football|Hongrie]]')
        pagetext = pagetext.replace('{{HUN football (1918-1919)}}', '[[Équipe de Hongrie de football|Hongrie]]')
        pagetext = pagetext.replace('{{HUN football (1920-1946)}}', '[[Équipe de Hongrie de football|Hongrie]]')
        pagetext = pagetext.replace('{{HUN football (1946-1949; 1956-1957)}}', '[[Équipe de Hongrie de football|Hongrie]]')
        pagetext = pagetext.replace('{{HUN football (1949-1956)}}', '[[Équipe de Hongrie de football|Hongrie]]')
        pagetext = pagetext.replace('{{HUN football -17}}', '[[Équipe de Hongrie de football des moins de 17 ans|Hongrie]]')
        pagetext = pagetext.replace('{{HUN football -21}}', '[[Équipe de Hongrie espoirs de football|Hongrie]]')
        pagetext = pagetext.replace('{{HUN football}}', '[[Équipe de Hongrie de football|Hongrie]]')
        pagetext = pagetext.replace('{{IMA football}}', '[[Équipe de l\'île de Man de football|Île de Man]]')
        pagetext = pagetext.replace('{{INA football (1934-1949)}}', '[[Équipe d\'Indonésie de football|Indes orientales néerlandaises]]')
        pagetext = pagetext.replace('{{INA football}}', '[[Équipe d\'Indonésie de football|Indonésie]]')
        pagetext = pagetext.replace('{{IND football}}', '[[Équipe d\'Inde de football|Inde]]')
        pagetext = pagetext.replace('{{IRI football (1925-1964)}}', '[[Équipe d\'Iran de football|Iran]]')
        pagetext = pagetext.replace('{{IRI football (1964-1980)}}', '[[Équipe d\'Iran de football|Iran]]')
        pagetext = pagetext.replace('{{IRI football}}', '[[Équipe d\'Iran de football|Iran]]')
        pagetext = pagetext.replace('{{IRL football (1922-1937)}}', '[[Équipe de République d\'Irlande de football|État libre d\'Irlande]]')
        pagetext = pagetext.replace('{{IRL football -21}}', '[[Équipe de République d\'Irlande espoirs de football|Irlande]]')
        pagetext = pagetext.replace('{{IRL football}}', '[[Équipe de République d\'Irlande de football|Irlande]]')
        pagetext = pagetext.replace('{{IRQ football (1921-1959)}}', '[[Équipe d\'Irak de football|Irak]]')
        pagetext = pagetext.replace('{{IRQ football (1959-1963)}}', '[[Équipe d\'Irak de football|Irak]]')
        pagetext = pagetext.replace('{{IRQ football (1963-1991)}}', '[[Équipe d\'Irak de football|Irak]]')
        pagetext = pagetext.replace('{{IRQ football (1991-2004)}}', '[[Équipe d\'Irak de football|Irak]]')
        pagetext = pagetext.replace('{{IRQ football (2004-2008)}}', '[[Équipe d\'Irak de football|Irak]]')
        pagetext = pagetext.replace('{{IRQ football}}', '[[Équipe d\'Irak de football|Irak]]')
        pagetext = pagetext.replace('{{ISL football -17}}', '[[Équipe d\'Islande de football des moins de 17 ans|Islande]]')
        pagetext = pagetext.replace('{{ISL football -21}}', '[[Équipe d\'Islande espoirs de football|Islande]]')
        pagetext = pagetext.replace('{{ISL football}}', '[[Équipe d\'Islande de football|Islande]]')
        pagetext = pagetext.replace('{{ISR football -21}}', '[[Équipe d\'Israël espoirs de football|Israël]]')
        pagetext = pagetext.replace('{{ISR football}}', '[[Équipe d\'Israël de football|Israël]]')
        pagetext = pagetext.replace('{{ISV football}}', '[[Équipe des îles Vierges des États-Unis de football|Îles Vierges des États-Unis]]')
        pagetext = pagetext.replace('{{ITA football (1861-1946)}}', '[[Équipe d\'Italie de football|Italie]]')
        pagetext = pagetext.replace('{{ITA football -17}}', '[[Équipe d\'Italie de football des moins de 17 ans|Italie]]')
        pagetext = pagetext.replace('{{ITA football -21}}', '[[Équipe d\'Italie espoirs de football|Italie]]')
        pagetext = pagetext.replace('{{ITA football}}', '[[Équipe d\'Italie de football|Italie]]')
        pagetext = pagetext.replace('{{IVB football}}', '[[Équipe des Îles Vierges britanniques de football|Îles Vierges britanniques]]')
        pagetext = pagetext.replace('{{JAM football}}', '[[Équipe de Jamaïque de football|Jamaïque]]')
        pagetext = pagetext.replace('{{JER football}}', '[[Équipe de Jersey de football|Jersey]]')
        pagetext = pagetext.replace('{{JOR football}}', '[[Équipe de Jordanie de football|Jordanie]]')
        pagetext = pagetext.replace('{{JPN football}}', '[[Équipe du Japon de football|Japon]]')
        pagetext = pagetext.replace('{{KAZ football (1953-1992)}}', '[[Équipe du Kazakhstan de football|Kazakhstan]]')
        pagetext = pagetext.replace('{{KAZ football -21}}', '[[Équipe du Kazakhstan espoirs de football|Kazakhstan]]')
        pagetext = pagetext.replace('{{KAZ football}}', '[[Équipe du Kazakhstan de football|Kazakhstan]]')
        pagetext = pagetext.replace('{{KEN football}}', '[[Équipe du Kenya de football|Kenya]]')
        pagetext = pagetext.replace('{{KGZ football}}', '[[Équipe du Kirghizistan de football|Kirghizistan]]')
        pagetext = pagetext.replace('{{KIR football}}', '[[Équipe des Kiribati de football|Kiribati]]')
        pagetext = pagetext.replace('{{KOR football -17}}', '[[Équipe de Corée du Sud de football des moins de 17 ans|Corée du Sud]]')
        pagetext = pagetext.replace('{{KOR football}}', '[[Équipe de Corée du Sud de football|Corée du Sud]]')
        pagetext = pagetext.replace('{{KOS football}}', '[[Équipe du Kosovo de football|Kosovo]]')
        pagetext = pagetext.replace('{{KSA football (1938-1973)}}', '[[Équipe d\'Arabie saoudite de football|Arabie saoudite]]')
        pagetext = pagetext.replace('{{KSA football -17}}', '[[Équipe d\'Arabie saoudite de football des moins de 17 ans|Arabie saoudite]]')
        pagetext = pagetext.replace('{{KSA football}}', '[[Équipe d\'Arabie saoudite de football|Arabie saoudite]]')
        pagetext = pagetext.replace('{{KUR football}}', '[[Équipe du Kurdistan de football|Kurdistan]]')
        pagetext = pagetext.replace('{{KUW football}}', '[[Équipe du Koweït de football|Koweït]]')
        pagetext = pagetext.replace('{{LAO football (1952-1975)}}', '[[Équipe du Laos de football|Laos]]')
        pagetext = pagetext.replace('{{LAO football}}', '[[Équipe du Laos de football|Laos]]')
        pagetext = pagetext.replace('{{LAT football -21}}', '[[Équipe de Lettonie espoirs de football|Lettonie]]')
        pagetext = pagetext.replace('{{LAT football}}', '[[Équipe de Lettonie de football|Lettonie]]')
        pagetext = pagetext.replace('{{LBA football (1951-1969)}}', '[[Équipe de Libye de football|Libye]]')
        pagetext = pagetext.replace('{{LBA football (1969-1972)}}', '[[Équipe de Libye de football|Libye]]')
        pagetext = pagetext.replace('{{LBA football (1972-1977)}}', '[[Équipe de Libye de football|Libye]]')
        pagetext = pagetext.replace('{{LBA football (1977-2011)}}', '[[Équipe de Libye de football|Libye]]')
        pagetext = pagetext.replace('{{LBA football}}', '[[Équipe de Libye de football|Libye]]')
        pagetext = pagetext.replace('{{LBR football}}', '[[Équipe du Liberia de football|Liberia]]')
        pagetext = pagetext.replace('{{LBY football -21}}', '[[Équipe de Libye espoirs de football|Libye]]')
        pagetext = pagetext.replace('{{LCA football}}', '[[Équipe de Sainte-Lucie de football|Sainte-Lucie]]')
        pagetext = pagetext.replace('{{LES football (1966-1987)}}', '[[Équipe du Lesotho de football|Lesotho]]')
        pagetext = pagetext.replace('{{LES football (1987-2006)}}', '[[Équipe du Lesotho de football|Lesotho]]')
        pagetext = pagetext.replace('{{LES football}}', '[[Équipe du Lesotho de football|Lesotho]]')
        pagetext = pagetext.replace('{{LIB football (1920-1943)}}', '[[Équipe du Liban de football|Liban]]')
        pagetext = pagetext.replace('{{LIB football -20}}', '[[Équipe du Liban de football des moins de 20 ans|Liban]]')
        pagetext = pagetext.replace('{{LIB football}}', '[[Équipe du Liban de football|Liban]]')
        pagetext = pagetext.replace('{{LIE football -21}}', '[[Équipe du Liechtenstein espoirs de football|Liechtenstein]]')
        pagetext = pagetext.replace('{{LIE football}}', '[[Équipe du Liechtenstein de football|Liechtenstein]]')
        pagetext = pagetext.replace('{{LTU football (1918-1940)}}', '[[Équipe de Lituanie de football|Lituanie]]')
        pagetext = pagetext.replace('{{LTU football (1990-2004)}}', '[[Équipe de Lituanie de football|Lituanie]]')
        pagetext = pagetext.replace('{{LTU football -20}}', '[[Équipe de Lituanie de football des moins de 20 ans|Lituanie]]')
        pagetext = pagetext.replace('{{LTU football -21}}', '[[Équipe de Lituanie espoirs de football|Lituanie]]')
        pagetext = pagetext.replace('{{LTU football}}', '[[Équipe de Lituanie de football|Lituanie]]')
        pagetext = pagetext.replace('{{LUX football -21}}', '[[Équipe du Luxembourg espoirs de football|Luxembourg]]')
        pagetext = pagetext.replace('{{LUX football}}', '[[Équipe du Luxembourg de football|Luxembourg]]')
        pagetext = pagetext.replace('{{MAC football (1949-1999)}}', '[[Équipe de Macao de football|Macao]]')
        pagetext = pagetext.replace('{{MAC football}}', '[[Équipe de Macao de football|Macao]]')
        pagetext = pagetext.replace('{{MAD football -20}}', '[[Équipe de Madagascar de football des moins de 20 ans|Madagascar]]')
        pagetext = pagetext.replace('{{MAD football}}', '[[Équipe de Madagascar de football|Madagascar]]')
        pagetext = pagetext.replace('{{MAE football}}', '[[Équipe de Madère de football|Madère]]')
        pagetext = pagetext.replace('{{MAF football}}', '[[Équipe de Saint-Martin de football|Saint-Martin]]')
        pagetext = pagetext.replace('{{MAL football}}', '[[Équipe de Malaisie de football|Malaya]]')
        pagetext = pagetext.replace('{{MAR football -20}}', '[[Équipe du Maroc de football des moins de 20 ans|Maroc]]')
        pagetext = pagetext.replace('{{MAR football}}', '[[Équipe du Maroc de football|Maroc]]')
        pagetext = pagetext.replace('{{MAS football}}', '[[Équipe de Malaisie de football|Malaisie]]')
        pagetext = pagetext.replace('{{MAW football (2010-2012)}}', '[[Équipe du Malawi de football|Malawi]]')
        pagetext = pagetext.replace('{{MAW football}}', '[[Équipe du Malawi de football|Malawi]]')
        pagetext = pagetext.replace('{{MDA football -21}}', '[[Équipe de Moldavie espoirs de football|Moldavie]]')
        pagetext = pagetext.replace('{{MDA football}}', '[[Équipe de Moldavie de football|Moldavie]]')
        pagetext = pagetext.replace('{{MDV football}}', '[[Équipe des Maldives de football|Maldives]]')
        pagetext = pagetext.replace('{{MEX football (1916-1934)}}', '[[Équipe du Mexique de football|Mexique]]')
        pagetext = pagetext.replace('{{MEX football (1934-1968)}}', '[[Équipe du Mexique de football|Mexique]]')
        pagetext = pagetext.replace('{{MEX football -17}}', '[[Équipe du Mexique de football des moins de 17 ans|Mexique]]')
        pagetext = pagetext.replace('{{MEX football -20}}', '[[Équipe du Mexique de football des moins de 20 ans|Mexique]]')
        pagetext = pagetext.replace('{{MEX football}}', '[[Équipe du Mexique de football|Mexique]]')
        pagetext = pagetext.replace('{{MGL football (1949-1992)}}', '[[Équipe de Mongolie de football|Mongolie]]')
        pagetext = pagetext.replace('{{MGL football}}', '[[Équipe de Mongolie de football|Mongolie]]')
        pagetext = pagetext.replace('{{MKD football (1991-1995)}}', '[[Équipe de Macédoine de football|Macédoine]]')
        pagetext = pagetext.replace('{{MKD football -21}}', '[[Équipe de Macédoine espoirs de football|Macédoine]]')
        pagetext = pagetext.replace('{{MKD football}}', '[[Équipe de Macédoine de football|Macédoine]]')
        pagetext = pagetext.replace('{{MLI football -20}}', '[[Équipe du Mali de football des moins de 20 ans|Mali]]')
        pagetext = pagetext.replace('{{MLI football}}', '[[Équipe du Mali de football|Mali]]')
        pagetext = pagetext.replace('{{MLT football -17}}', '[[Équipe de Malte de football des moins de 17 ans|Malte]]')
        pagetext = pagetext.replace('{{MLT football -21}}', '[[Équipe de Malte espoirs de football|Malte]]')
        pagetext = pagetext.replace('{{MLT football}}', '[[Équipe de Malte de football|Malte]]')
        pagetext = pagetext.replace('{{MNE football -21}}', '[[Équipe du Monténégro espoirs de football|Monténégro]]')
        pagetext = pagetext.replace('{{MNE football}}', '[[Équipe du Monténégro de football|Monténégro]]')
        pagetext = pagetext.replace('{{MNP football}}', '[[Équipe des îles Mariannes du Nord de football|Îles Mariannes du Nord]]')
        pagetext = pagetext.replace('{{MON football}}', '[[Équipe de Monaco de football|Monaco]]')
        pagetext = pagetext.replace('{{MOZ football (1974-1975)}}', '[[Équipe du Mozambique de football|Mozambique]]')
        pagetext = pagetext.replace('{{MOZ football (1975-1983)}}', '[[Équipe du Mozambique de football|Mozambique]]')
        pagetext = pagetext.replace('{{MOZ football}}', '[[Équipe du Mozambique de football|Mozambique]]')
        pagetext = pagetext.replace('{{MRI football (1923-1968)}}', '[[Équipe de Maurice de football|Maurice]]')
        pagetext = pagetext.replace('{{MRI football}}', '[[Équipe de Maurice de football|Maurice]]')
        pagetext = pagetext.replace('{{MSR football}}', '[[Équipe de Montserrat de football|Montserrat]]')
        pagetext = pagetext.replace('{{MTN football}}', '[[Équipe de Mauritanie de football|Mauritanie]]')
        pagetext = pagetext.replace('{{MTQ football}}', '[[Équipe de Martinique de football|Martinique]]')
        pagetext = pagetext.replace('{{MWI football}}', '[[Équipe du Malawi de football|Malawi]]')
        pagetext = pagetext.replace('{{MYA football (1948-1974)}}', '[[Équipe de Birmanie de football|Birmanie]]')
        pagetext = pagetext.replace('{{MYA football (1974-2010)}}', '[[Équipe de Birmanie de football|Birmanie]]')
        pagetext = pagetext.replace('{{MYA football féminin 1974}}', '[[Équipe de Birmanie féminine de football|Birmanie]]')
        pagetext = pagetext.replace('{{MYA football}}', '[[Équipe de Birmanie de football|Birmanie]]')
        pagetext = pagetext.replace('{{MYT football}}', '[[Équipe de Mayotte de football|Mayotte]]')
        pagetext = pagetext.replace('{{NAM football}}', '[[Équipe de Namibie de football|Namibie]]')
        pagetext = pagetext.replace('{{NAV football}}', '[[Équipe de Navarre de football|Navarre]]')
        pagetext = pagetext.replace('{{NCA football}}', '[[Équipe du Nicaragua de football|Nicaragua]]')
        pagetext = pagetext.replace('{{NCL football}}', '[[Équipe de Nouvelle-Calédonie de football|Nouvelle-Calédonie]]')
        pagetext = pagetext.replace('{{NCY football}}', '[[Équipe de République turque de Chypre du Nord de football|Chypre du Nord]]')
        pagetext = pagetext.replace('{{NED football -17}}', '[[Équipe des Pays-Bas de football des moins de 17 ans|Pays-Bas]]')
        pagetext = pagetext.replace('{{NED football -21}}', '[[Équipe des Pays-Bas espoirs de football|Pays-Bas]]')
        pagetext = pagetext.replace('{{NED football}}', '[[Équipe des Pays-Bas de football|Pays-Bas]]')
        pagetext = pagetext.replace('{{NEP football}}', '[[Équipe du Népal de football|Népal]]')
        pagetext = pagetext.replace('{{NFK football}}', '[[Équipe de l\'Île Norfolk de football|Île Norfolk]]')
        pagetext = pagetext.replace('{{NGA football -17}}', '[[Équipe du Nigeria de football des moins de 17 ans|Nigéria]]')
        pagetext = pagetext.replace('{{NGR football (1914-1960)}}', '[[Équipe du Nigeria de football|Nigeria]]')
        pagetext = pagetext.replace('{{NGR football}}', '[[Équipe du Nigeria de football|Nigeria]]')
        pagetext = pagetext.replace('{{NIG football -20}}', '[[Équipe du Niger de football des moins de 20 ans|Niger]]')
        pagetext = pagetext.replace('{{NIG football}}', '[[Équipe du Niger de football|Niger]]')
        pagetext = pagetext.replace('{{NIR football -21}}', '[[Équipe d\'Irlande du Nord espoirs de football|Irlande du Nord]]')
        pagetext = pagetext.replace('{{NIR football}}', '[[Équipe d\'Irlande du Nord de football|Irlande du Nord]]')
        pagetext = pagetext.replace('{{NIU football}}', '[[Équipe de Niue de football|Niue]]')
        pagetext = pagetext.replace('{{NOR football -21}}', '[[Équipe de Norvège espoirs de football|Norvège]]')
        pagetext = pagetext.replace('{{NOR football}}', '[[Équipe de Norvège de football|Norvège]]')
        pagetext = pagetext.replace('{{NRH football}}', '[[Équipe de Zambie de football|Rhodésie du Nord]]')
        pagetext = pagetext.replace('{{NRU football}}', '[[Équipe de Nauru de football|Nauru]]')
        pagetext = pagetext.replace('{{NYE football}}', '[[Équipe du Yémen de football|Yémen du Nord]]')
        pagetext = pagetext.replace('{{NZL football}}', '[[Équipe de Nouvelle-Zélande de football|Nouvelle-Zélande]]')
        pagetext = pagetext.replace('{{OCC football}}', '[[Équipe d\'Occitanie de football|Occitanie]]')
        pagetext = pagetext.replace('{{OMA football (1856-1970)}}', '[[Équipe d\'Oman de football|Mascate et Oman]]')
        pagetext = pagetext.replace('{{OMA football (1970-1995)}}', '[[Équipe d\'Oman de football|Oman]]')
        pagetext = pagetext.replace('{{OMA football}}', '[[Équipe d\'Oman de football|Oman]]')
        pagetext = pagetext.replace('{{PAD football}}', '[[Équipe de Padanie de football|Padanie]]')
        pagetext = pagetext.replace('{{PAK football}}', '[[Équipe du Pakistan de football|Pakistan]]')
        pagetext = pagetext.replace('{{PAN football}}', '[[Équipe du Panama de football|Panama]]')
        pagetext = pagetext.replace('{{PAR football (1842-1954)}}', '[[Équipe du Paraguay de football|Paraguay]]')
        pagetext = pagetext.replace('{{PAR football (1954-1988)}}', '[[Équipe du Paraguay de football|Paraguay]]')
        pagetext = pagetext.replace('{{PAR football (1988-1990)}}', '[[Équipe du Paraguay de football|Paraguay]]')
        pagetext = pagetext.replace('{{PAR football (1990-2013)}}', '[[Équipe du Paraguay de football|Paraguay]]')
        pagetext = pagetext.replace('{{PAR football}}', '[[Équipe du Paraguay de football|Paraguay]]')
        pagetext = pagetext.replace('{{PCN football}}', '[[Équipe des îles Pitcairn de football|Îles Pitcairn]]')
        pagetext = pagetext.replace('{{PER football (1825-1950)}}', '[[Équipe du Pérou de football|Pérou]]')
        pagetext = pagetext.replace('{{PER football}}', '[[Équipe du Pérou de football|Pérou]]')
        pagetext = pagetext.replace('{{PHI football}}', '[[Équipe des Philippines de football|Philippines]]')
        pagetext = pagetext.replace('{{PLE football}}', '[[Équipe de Palestine de football|Palestine]]')
        pagetext = pagetext.replace('{{PLW football}}', '[[Équipe des Palaos de football|Palaos]]')
        pagetext = pagetext.replace('{{PNG football}}', '[[Équipe de Papouasie-Nouvelle-Guinée de football|Papouasie-Nouvelle-Guinée]]')
        pagetext = pagetext.replace('{{POL football -17}}', '[[Équipe de Pologne de football des moins de 17 ans|Pologne]]')
        pagetext = pagetext.replace('{{POL football -21}}', '[[Équipe de Pologne espoirs de football|Pologne]]')
        pagetext = pagetext.replace('{{POL football}}', '[[Équipe de Pologne de football|Pologne]]')
        pagetext = pagetext.replace('{{POR football -17}}', '[[Équipe du Portugal de football des moins de 17 ans|Portugal]]')
        pagetext = pagetext.replace('{{POR football -20}}', '[[Équipe du Portugal de football des moins de 20 ans|Portugal U-20]]')
        pagetext = pagetext.replace('{{POR football -21}}', '[[Équipe du Portugal espoirs de football|Portugal]]')
        pagetext = pagetext.replace('{{POR football}}', '[[Équipe du Portugal de football|Portugal]]')
        pagetext = pagetext.replace('{{PRK football}}', '[[Équipe de Corée du Nord de football|Corée du Nord]]')
        pagetext = pagetext.replace('{{PUR football}}', '[[Équipe de Porto Rico de football|Porto Rico]]')
        pagetext = pagetext.replace('{{QAT football (1949-1971)}}', '[[Équipe du Qatar de football|Qatar]]')
        pagetext = pagetext.replace('{{QAT football -17}}', '[[Équipe du Qatar de football des moins de 17 ans|Qatar]]')
        pagetext = pagetext.replace('{{QAT football -21}}', '[[Équipe du Qatar espoirs de football|Qatar]]')
        pagetext = pagetext.replace('{{QAT football}}', '[[Équipe du Qatar de football|Qatar]]')
        pagetext = pagetext.replace('{{QUE football}}', '[[Équipe du Québec de football|Québec]]')
        pagetext = pagetext.replace('{{RDC football -20}}', '[[Équipe de République démocratique du Congo de football des moins de 20 ans|République démocratique du Congo]]')
        pagetext = pagetext.replace('{{REU football}}', '[[Équipe de La Réunion de football|La Réunion]]')
        pagetext = pagetext.replace('{{RFY football}}', '[[Équipe de Serbie de football|RF Yougoslavie]]')
        pagetext = pagetext.replace('{{RHO football (1964-1968)}}', '[[Équipe du Zimbabwe de football|Rhodésie]]')
        pagetext = pagetext.replace('{{RHO football}}', '[[Équipe du Zimbabwe de football|Rhodésie]]')
        pagetext = pagetext.replace('{{ROD football}}', '[[Équipe de Rhodes de football|Rhodes]]')
        pagetext = pagetext.replace('{{ROU football (1948-1952)}}', '[[Équipe de Roumanie de football|Roumanie]]')
        pagetext = pagetext.replace('{{ROU football (1952-1965)}}', '[[Équipe de Roumanie de football|Roumanie]]')
        pagetext = pagetext.replace('{{ROU football (1965-1989)}}', '[[Équipe de Roumanie de football|Roumanie]]')
        pagetext = pagetext.replace('{{ROU football -21}}', '[[Équipe de Roumanie espoirs de football|Roumanie]]')
        pagetext = pagetext.replace('{{ROU football}}', '[[équipe de Roumanie de football|Roumanie]]')
        pagetext = pagetext.replace('{{RSA football (1928-1994)}}', '[[Équipe d\'Afrique du Sud de football|Afrique du Sud]]')
        pagetext = pagetext.replace('{{RSA football}}', '[[Équipe d\'Afrique du Sud de football|Afrique du Sud]]')
        pagetext = pagetext.replace('{{RUS football -21}}', '[[Équipe de Russie espoirs de football|Russie]]')
        pagetext = pagetext.replace('{{RUS football}}', '[[Équipe de Russie de football|Russie]]')
        pagetext = pagetext.replace('{{RWA football (1962-2001)}}', '[[Équipe du Rwanda de football|Rwanda]]')
        pagetext = pagetext.replace('{{RWA football -20}}', '[[Équipe du Rwanda de football des moins de 20 ans|Rwanda]]')
        pagetext = pagetext.replace('{{RWA football}}', '[[Équipe du Rwanda de football|Rwanda]]')
        pagetext = pagetext.replace('{{SAA football}}', '[[Équipe de Sarre de football|Sarre]]')
        pagetext = pagetext.replace('{{SAK football}}', '[[Équipe de Sercq de football|Sercq]]')
        pagetext = pagetext.replace('{{SAM football (1979-1997)}}', '[[Équipe des Samoa de football|Samoa occidentales]]')
        pagetext = pagetext.replace('{{SAM football}}', '[[Équipe des Samoa de football|Samoa]]')
        pagetext = pagetext.replace('{{SAP football}}', '[[Équipe de Laponie de football|Laponie]]')
        pagetext = pagetext.replace('{{SBR football}}', '[[Équipe de République serbe de Bosnie de football|Rép. serbe de Bosnie]]')
        pagetext = pagetext.replace('{{SBY football}}', '[[Équipe de Saint-Barthélémy de football|Saint-Barthélémy]]')
        pagetext = pagetext.replace('{{SCG football -21}}', '[[Équipe de Serbie-et-Monténégro espoirs de football|Serbie-et-Monténégro]]')
        pagetext = pagetext.replace('{{SCG football}}', '[[Équipe de Serbie-et-Monténégro de football|Serbie-et-Monténégro]]')
        pagetext = pagetext.replace('{{SCO football -17}}', '[[Équipe d\'Écosse de football des moins de 17 ans|Écosse]]')
        pagetext = pagetext.replace('{{SCO football -21}}', '[[Équipe d\'Écosse espoirs de football|Écosse]]')
        pagetext = pagetext.replace('{{SCO football}}', '[[Équipe d\'Écosse de football|Écosse]]')
        pagetext = pagetext.replace('{{SEA football}}', '[[Équipe de Sealand de football|Sealand]]')
        pagetext = pagetext.replace('{{SEN football -20}}', '[[Équipe du Sénégal de football des moins de 20 ans|Sénégal]]')
        pagetext = pagetext.replace('{{SEN football}}', '[[Équipe du Sénégal de football|Sénégal]]')
        pagetext = pagetext.replace('{{SEY football (1961-1976)}}', '[[Équipe des Seychelles de football|Seychelles]]')
        pagetext = pagetext.replace('{{SEY football (1976-1977)}}', '[[Équipe des Seychelles de football|Seychelles]]')
        pagetext = pagetext.replace('{{SEY football (1977-1996)}}', '[[Équipe des Seychelles de football|Seychelles]]')
        pagetext = pagetext.replace('{{SEY football}}', '[[Équipe des Seychelles de football|Seychelles]]')
        pagetext = pagetext.replace('{{SHE football}}', '[[Équipe des îles Shetland de football|Îles Shetland]]')
        pagetext = pagetext.replace('{{SIA football}}', '[[Équipe de Thaïlande de football|Siam]]')
        pagetext = pagetext.replace('{{SIK football}}', '[[Équipe du Sikkim de football|Sikkim]]')
        pagetext = pagetext.replace('{{SIL football}}', '[[Équipe de Silésie de football|Silésie]]')
        pagetext = pagetext.replace('{{SIN football (1946-1959)}}', '[[Équipe de Singapour de football|Singapour]]')
        pagetext = pagetext.replace('{{SIN football}}', '[[Équipe de Singapour de football|Singapour]]')
        pagetext = pagetext.replace('{{SKN football}}', '[[Équipe de Saint-Christophe-et-Niévès de football|Saint-Christophe-et-Niévès]]')
        pagetext = pagetext.replace('{{SLE football (1916-1961)}}', '[[Équipe de Sierra Leone de football|Sierra Leone]]')
        pagetext = pagetext.replace('{{SLE football}}', '[[Équipe de Sierra Leone de football|Sierra Leone]]')
        pagetext = pagetext.replace('{{SLO football -21}}', '[[Équipe de Slovénie espoirs de football|France]]')
        pagetext = pagetext.replace('{{SLO football}}', '[[Équipe de Slovénie de football|Slovénie]]')
        pagetext = pagetext.replace('{{SMD football}}', '[[Équipe du Somaliland de football|Somaliland]]')
        pagetext = pagetext.replace('{{SMR football -21}}', '[[Équipe de Saint-Marin espoirs de football|Saint-Marin]]')
        pagetext = pagetext.replace('{{SMR football}}', '[[Équipe de Saint-Marin de football|Saint-Marin]]')
        pagetext = pagetext.replace('{{SOL football}}', '[[Équipe des Salomon de football|Salomon]]')
        pagetext = pagetext.replace('{{SOM football}}', '[[Équipe de Somalie de football|Somalie]]')
        pagetext = pagetext.replace('{{SPM football}}', '[[Équipe de Saint-Pierre-et-Miquelon de football|Saint-Pierre-et-Miquelon]]')
        pagetext = pagetext.replace('{{SRB football -21}}', '[[Équipe de Serbie espoirs de football|Serbie]]')
        pagetext = pagetext.replace('{{SRB football}}', '[[Équipe de Serbie de football|Serbie]]')
        pagetext = pagetext.replace('{{SRH football}}', '[[Équipe du Zimbabwe de football|Rhodésie du Sud]]')
        pagetext = pagetext.replace('{{SRI football (1951-1972)}}', '[[Équipe du Sri Lanka de football|Ceylan]]')
        pagetext = pagetext.replace('{{SRI football}}', '[[Équipe du Sri Lanka de football|Sri Lanka]]')
        pagetext = pagetext.replace('{{SRM football}}', '[[Équipe de Saaremaa de football|Saaremaa]]')
        pagetext = pagetext.replace('{{SSD football}}', '[[Équipe du Soudan du Sud de football|Soudan du Sud]]')
        pagetext = pagetext.replace('{{STM football}}', '[[Équipe de Saint-Martin de football|Saint-Martin]]')
        pagetext = pagetext.replace('{{STP football}}', '[[Équipe de Sao Tomé-et-Principe de football|Sao Tomé-et-Principe]]')
        pagetext = pagetext.replace('{{SUD football (1956-1970)}}', '[[Équipe du Soudan de football|Soudan]]')
        pagetext = pagetext.replace('{{SUD football}}', '[[Équipe du Soudan de football|Soudan]]')
        pagetext = pagetext.replace('{{SUI football -17}}', '[[Équipe de Suisse de football des moins de 17 ans|Suisse]]')
        pagetext = pagetext.replace('{{SUI football -21}}', '[[Équipe de Suisse espoirs de football|Suisse]]')
        pagetext = pagetext.replace('{{SUI football}}', '[[Équipe de Suisse de football|Suisse]]')
        pagetext = pagetext.replace('{{SUR football (1920-1959)}}', '[[Équipe du Suriname de football|Guyane néerlandaise]]')
        pagetext = pagetext.replace('{{SUR football (1959-1975)}}', '[[Équipe du Suriname de football|Suriname]]')
        pagetext = pagetext.replace('{{SUR football}}', '[[Équipe du Suriname de football|Suriname]]')
        pagetext = pagetext.replace('{{SVK football (1939-1945)}}', '[[Équipe de Slovaquie de football|Slovaquie]]')
        pagetext = pagetext.replace('{{SVK football -21}}', '[[Équipe de Slovaquie espoirs de football|Slovaquie]]')
        pagetext = pagetext.replace('{{SVK football}}', '[[Équipe de Slovaquie de football|Slovaquie]]')
        pagetext = pagetext.replace('{{SVN football -17}}', '[[Équipe de Slovénie de football des moins de 17 ans|Slovénie]]')
        pagetext = pagetext.replace('{{SWE football -21}}', '[[Équipe de Suède espoirs de football|Suède]]')
        pagetext = pagetext.replace('{{SWE football}}', '[[Équipe de Suède de football|Suède]]')
        pagetext = pagetext.replace('{{SWZ football}}', '[[Équipe du Swaziland de football|Swaziland]]')
        pagetext = pagetext.replace('{{SXM football}}', '[[Équipe de Sint Maarten de football|Sint Maarten]]')
        pagetext = pagetext.replace('{{SYE football}}', '[[Équipe du Yémen du Sud de football|Yémen du Sud]]')
        pagetext = pagetext.replace('{{SYR football (1932-1958; 1961-1963)}}', '[[Équipe de Syrie de football|Syrie]]')
        pagetext = pagetext.replace('{{SYR football (1963-1972)}}', '[[Équipe de Syrie de football|Syrie]]')
        pagetext = pagetext.replace('{{SYR football (1972-1980)}}', '[[Équipe de Syrie de football|Syrie]]')
        pagetext = pagetext.replace('{{SYR football -21}}', '[[Équipe de Syrie espoirs de football|Syrie]]')
        pagetext = pagetext.replace('{{SYR football}}', '[[Équipe de Syrie de football|Syrie]]')
        pagetext = pagetext.replace('{{TAH football}}', '[[Équipe de Tahiti de football|Tahiti]]')
        pagetext = pagetext.replace('{{TAN football (1919-1961)}}', '[[Équipe de Tanzanie de football|Tanganyika]]')
        pagetext = pagetext.replace('{{TAN football (1961-1964)}}', '[[Équipe de Tanzanie de football|Tanganyika]]')
        pagetext = pagetext.replace('{{TAN football}}', '[[Équipe de Tanzanie de football|Tanzanie]]')
        pagetext = pagetext.replace('{{TCA football}}', '[[Équipe des îles Turques-et-Caïques de football|Îles Turques-et-Caïques]]')
        pagetext = pagetext.replace('{{TCH football -21}}', '[[Équipe de Tchécoslovaquie espoirs de football|Tchécoslovaquie]]')
        pagetext = pagetext.replace('{{TCH football}}', '[[Équipe de Tchécoslovaquie de football|Tchécoslovaquie]]')
        pagetext = pagetext.replace('{{TCT football}}', '[[Équipe de Tchétchénie de football|Tchétchénie]]')
        pagetext = pagetext.replace('{{TGA football}}', '[[Équipe des Tonga de football|Tonga]]')
        pagetext = pagetext.replace('{{THA football}}', '[[Équipe de Thaïlande de football|Thaïlande]]')
        pagetext = pagetext.replace('{{TIB football}}', '[[Équipe du Tibet de football|Tibet]]')
        pagetext = pagetext.replace('{{TJK football}}', '[[Équipe du Tadjikistan de football|Tadjikistan]]')
        pagetext = pagetext.replace('{{TKM football (1953-1992)}}', '[[Équipe du Turkménistan de football|Turkménistan]]')
        pagetext = pagetext.replace('{{TKM football (1992-1997)}}', '[[Équipe du Turkménistan de football|Turkménistan]]')
        pagetext = pagetext.replace('{{TKM football (1997-2001)}}', '[[Équipe du Turkménistan de football|Turkménistan]]')
        pagetext = pagetext.replace('{{TKM football}}', '[[Équipe du Turkménistan de football|Turkménistan]]')
        pagetext = pagetext.replace('{{TLS football}}', '[[Équipe du Timor oriental de football|Timor oriental]]')
        pagetext = pagetext.replace('{{TOG football}}', '[[Équipe du Togo de football|Togo]]')
        pagetext = pagetext.replace('{{TPE football}}', '[[Équipe de Taipei chinois de football|Taïwan]]')
        pagetext = pagetext.replace('{{TRI football}}', '[[Équipe de Trinité-et-Tobago de football|Trinité-et-Tobago]]')
        pagetext = pagetext.replace('{{TUN football -21}}', '[[Équipe de Tunisie olympique de football|Tunisie]]')
        pagetext = pagetext.replace('{{TUN football}}', '[[Équipe de Tunisie de football|Tunisie]]')
        pagetext = pagetext.replace('{{TUR football -17}}', '[[Équipe de Turquie de football des moins de 17 ans|Turquie]]')
        pagetext = pagetext.replace('{{TUR football -21}}', '[[Équipe de Turquie espoirs de football|Turquie]]')
        pagetext = pagetext.replace('{{TUR football}}', '[[Équipe de Turquie de football|Turquie]]')
        pagetext = pagetext.replace('{{TUV football}}', '[[Équipe des Tuvalu de football|Tuvalu]]')
        pagetext = pagetext.replace('{{TWN football}}', '[[Équipe de Taipei chinois de football|Taïwan]]')
        pagetext = pagetext.replace('{{UAE football -21}}', '[[Équipe des Émirats Arabes Unis espoirs de football|Émirats Arabes Unis]]')
        pagetext = pagetext.replace('{{UAE football}}', '[[Équipe des Émirats arabes unis de football|Émirats arabes unis]]')
        pagetext = pagetext.replace('{{UAR football}}', '[[Équipe d\'Égypte de football|Rép. arabe unie]]')
        pagetext = pagetext.replace('{{UGA football}}', '[[Équipe d\'Ouganda de football|Ouganda]]')
        pagetext = pagetext.replace('{{UKR football -21}}', '[[Équipe d\'Ukraine espoirs de football|Ukraine]]')
        pagetext = pagetext.replace('{{UKR football}}', '[[Équipe d\'Ukraine de football|Ukraine]]')
        pagetext = pagetext.replace('{{UPV football}}', '[[Équipe du Burkina Faso de football|Haute-Volta]]')
        pagetext = pagetext.replace('{{URS football (1923-1955)}}', '[[Équipe d\'Union soviétique de football|Union soviétique]]')
        pagetext = pagetext.replace('{{URS football (1955-1980)}}', '[[Équipe d\'Union soviétique de football|Union soviétique]]')
        pagetext = pagetext.replace('{{URS football -17}}', '[[Équipe d\'URSS de football des moins de 17 ans|URSS]]')
        pagetext = pagetext.replace('{{URS football}}', '[[Équipe d\'Union soviétique de football|Union soviétique]]')
        pagetext = pagetext.replace('{{URU football}}', '[[Équipe d\'Uruguay de football|Uruguay]]')
        pagetext = pagetext.replace('{{USA football (1912-1959)}}', '[[Équipe des États-Unis de soccer|États-Unis]]')
        pagetext = pagetext.replace('{{USA football (1959-1960)}}', '[[Équipe des États-Unis de soccer|États-Unis]]')
        pagetext = pagetext.replace('{{USA football -17}}', '[[Équipe des États-Unis de soccer des moins de 17 ans|États-Unis]]')
        pagetext = pagetext.replace('{{USA football}}', '[[Équipe des États-Unis de soccer|États-Unis]]')
        pagetext = pagetext.replace('{{UZB football}}', '[[Équipe d\'Ouzbékistan de football|Ouzbékistan]]')
        pagetext = pagetext.replace('{{VAC football}}', '[[Équipe de la Communauté Valencienne de football|Communauté Valencienne]]')
        pagetext = pagetext.replace('{{VAN football}}', '[[Équipe du Vanuatu de football|Vanuatu]]')
        pagetext = pagetext.replace('{{VAT football}}', '[[Équipe du Vatican de football|Vatican]]')
        pagetext = pagetext.replace('{{VEN football (1930-1954)}}', '[[Équipe du Venezuela de football|Venezuela]]')
        pagetext = pagetext.replace('{{VEN football (1954-2006)}}', '[[Équipe du Venezuela de football|Venezuela]]')
        pagetext = pagetext.replace('{{VEN football}}', '[[Équipe du Venezuela de football|Venezuela]]')
        pagetext = pagetext.replace('{{VIE football}}', '[[Équipe du Viêt Nam de football|Viêt Nam]]')
        pagetext = pagetext.replace('{{VIN football}}', '[[Équipe de Saint-Vincent-et-les-Grenadines de football|Saint-Vincent-et-les-Grenadines]]')
        pagetext = pagetext.replace('{{VNO football}}', '[[Équipe du Viêt Nam de football|Nord-Viêt Nam]]')
        pagetext = pagetext.replace('{{VSO football}}', '[[Équipe du Sud-Vietnam de football|Sud-Vietnam]]')
        pagetext = pagetext.replace('{{WAL football -21}}', '[[Équipe du pays de Galles espoirs de football|Pays de Galles]]')
        pagetext = pagetext.replace('{{WAL football}}', '[[Équipe du pays de Galles de football|Pays de Galles]]')
        pagetext = pagetext.replace('{{WGT football}}', '[[Équipe de l\'île de Wight de football|Île de Wrght]]')
        pagetext = pagetext.replace('{{WLF football}}', '[[Équipe de Wallis-et-Futuna de football|Wallis-et-Futuna]]')
        pagetext = pagetext.replace('{{YEM football}}', '[[Équipe du Yémen de football|Yémen]]')
        pagetext = pagetext.replace('{{YUG football (1918-1941)}}', '[[Équipe de Yougoslavie de football|Yougoslavie]]')
        pagetext = pagetext.replace('{{YUG football}}', '[[Équipe de Yougoslavie de football|Yougoslavie]]')
        pagetext = pagetext.replace('{{YYM football}}', '[[Équipe d\'Anglesey de football|Anglesey]]')
        pagetext = pagetext.replace('{{ZAI football}}', '[[Équipe de République démocratique du Congo de football|Zaïre]]')
        pagetext = pagetext.replace('{{ZAM football}}', '[[Équipe de Zambie de football|Zambie]]')
        pagetext = pagetext.replace('{{ZAN football}}', '[[Équipe de Zanzibar de football|Zanzibar]]')
        pagetext = pagetext.replace('{{ZIM football}}', '[[Équipe du Zimbabwe de football|Zimbabwe]]')

        return pagetext
        
    def treat(self, page, item):
        
        """Process a single page/item."""
        if willstop:
            raise KeyboardInterrupt
        self.current_page = page
        
        #param -b
        titre = page.title()
        if self.param_first is not None:
            if self.param_first in titre:
                self.param_first = None
            else:
                pywikibot.output('Skipping')
                return
                
        item.get()
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
                    if not field.isdigit():
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
                            if re.search(r'{{[A-Z][A-Z][A-Z] football',value):
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
                        skip = False
                        qualif = qualif.replace ('–', '-')
                        qualif = qualif.replace ('&ndash;', '-')
                        qualif = qualif.replace ('avant ', '-')
                        #qualif = qualif.replace ('{{Clr}}', '')
                        #qualif = qualif.replace ('{{Year|', '')
                        #qualif = qualif.replace ('{{prêt}}', '')
                        qualif = re.sub(r'<ref.*<\/ref>', '', qualif)
                        qualif = re.sub(r'<ref.*\/ *>', '', qualif)            
                        qualif = re.sub(r'{{0(\|0+)?}}', '', qualif)
                        qualif = re.sub(r'[a-zA-Zéêû&; \.\[\?\]\{\}\|]', '', qualif)
                        #si pas de tiret, 
                        if (qualif.find('-') == -1): 
                            qualif = qualif + '-' + qualif 
                        dates = qualif.split('-')
                        wp_debut = ''
                        wp_fin = ''
                        qualifier_debut = None
                        qualifier_fin = None
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
                                                pywikibot.output(color_format(
                                                    '{yellow}Error - date fin à 2 chiffres : %s %s'
                                                    % (value, dates[1])))
                                        else:
                                            pywikibot.output(color_format(
                                                '{yellow}Error - date fin pas numérique : %s %s'
                                                % (value, dates[1])))
                                else:
                                    pywikibot.output(color_format(
                                        '{yellow}Error - date début à 2 chiffres : %s %s'
                                        % (value, dates[0])))
                            else:
                                pywikibot.output(color_format(
                                    '{yellow}Error - date début pas numérique : %s %s'
                                    % (value, dates[0])))
                            
                        if claim.getID() in item.claims:
                            existing_claims = item.claims[claim.getID()]  # Existing claims on page of same property
                
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
                                        if qualifier_debut is not None:
                                            existing.addQualifier(qualifier_debut)
                                            pywikibot.output(color_format('{green}adding %s as a qualifier of %s'
                                                % (wp_debut,value)))
                                        if qualifier_fin is not None:
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
                            if qualifier_debut is not None:
                                claim.addQualifier(qualifier_debut)
                            if qualifier_fin is not None:
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
