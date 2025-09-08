Skip to main contentSkip to article
ScienceDirect
  * Journals & Books


  *   * 




  * View **PDF**
  * Download full issue


Search ScienceDirect
## Outline
  1. Abstract
  2. Keywords
  3. 1. Introduction
  4. 2. Materials and methods
  5. 3. Results
  6. 4. Discussion
  7. 5. Conclusion
  8. Ethical approval
  9. Declaration of Competing Interest
  10. Acknowledgements
  11. Appendix A. Supplementary material
  12. Research Data
  13. References


## Figures (3)
  1. 
  2. 
  3. 


## Tables (2)
  1. Table 1
  2. Table 2


## Extras (2)
  1. Download all 
  2. Supplementary material
  3. Supplementary material



## Global Ecology and Conservation
Volume 54, October 2024, e03060

# Land use and oriental pied-hornbill occurrence in Singapore
Author links open overlay panelZaheedah Yahya a, Min Yi Chin b, Adlan Syaddad b, Philip Johns b 1
Show more
Outline
Add to Mendeley
Share
Cite
https://doi.org/10.1016/j.gecco.2024.e03060Get rights and content
Under a Creative Commons license
## Abstract
Oriental Pied-Hornbills (_Anthracoceros albirostris)_ disappeared from Singapore in the 1800s but were returned in the 2000s through a combination of active reintroduction and recolonization. Since then, they have multiplied and even thrived in Singapore, spreading throughout much of the country. Singapore is extremely urban and densely populated, and here we examine where hornbills have been seen as a function of land-use. We combine citizen science data from eBird and iNaturalist with GIS information to model hornbill occurrence. We find that vegetation with no canopy, marshy habitat, and built-up areas have strong positive effects on the probability of hornbill sightings. We interpret our results with respect to larger regional patterns.
  * Previous article in issue
  * Next article in issue


## Keywords
_Anthracoceros albirostris_
Citizen science
Species distribution model
Urban wildlife
## 1. Introduction
Southeast Asia includes multiple biodiversity hotspots (De Bruyn et al., 2014) but also has one of the highest deforestation rates (Hughes, 2017). Within Southeast Asia, intense urbanization and deforestation have resulted in substantial biodiversity loss in Singapore in particular (Corlett, 1992, Chisholm et al., 2023). While birds may be less dependent on Singapore’s nature reserves than other animals (Brook et al., 2003; but see Chisholm et al., 2023), some Singapore bird species have gone locally extinct. The Oriental Pied-Hornbill (_Anthracoceros albirostris)_ disappeared from Singapore in the 1800s, and the comprehensive checklist published by Gibson-Hill (1949) did not include these hornbills, even though this species survived in Peninsular Malaysia. In March 1994, after more than a century of absence, a pair was observed at Pulau Ubin, an island in Singapore’s northeast (Wong, 2011).
In 2006, Singapore’s National Parks Board (www.nparks.gov.sg) and the Wildlife Reserves of Singapore (now Mandai Wildlife Reserves; www.mandai.com/en/singapore-zoo.html) started the Singapore Hornbill Project to reintroduce the hornbills to Singapore (Cremades and Ng, 2012). The team set up artificial nests in previously unoccupied areas, such as southern Bukit Timah (Cremades et al., 2011). The program established populations in Bukit Timah, Pulau Ubin, and Singapore Botanic Garden within a few years (Cremades and Ng, 2012). Some hornbills can survive well in disturbed and fragmented habitats (Marsden and Pilgrim, 2002). Their successful adaptation to Singapore’s urban landscape is partly due to their use of cultivated fruits and other species found in urban parks and gardens (Lok et al., 2013, Tan, 2010), and may be aided by their ability to find food sources like other birds’ nestlings in an urban environment (Loong et al., 2021).
Although the Singapore Hornbill Project was a success, the Singapore Red Data Book lists the species as “Near Threatened” (www.nparks.gov.sg/biodiversity/wildlife-in-singapore/species-list/bird) as of March 2024. Exploring the occupancy of Oriental Pied-Hornbills, and relating hornbill sightings to land-use, has general implications to their reintroduction and colonization into urban environments.
Species distribution modelling (SDM) investigates relationships between species observations and environmental variables, assuming a functional relationship (Miller, 2010), and often using geographical information systems (GIS; Trisurat et al., 2013). Other studies of the Oriental Pied-Hornbills in Singapore used sighting density maps derived from citizen science platforms to explore population distribution (Strange and O’Dempsey, 2022). Citizen or community science platforms, such as eBird (Sullivan et al., 2009) and iNaturalist, can serve as repositories for observations of hornbills, especially in urban areas with high human density and many participants. These platforms include metadata such as date, time and location, which allow the validation of observations through the citizen science community. Although there are potential biases, these databases can offer a viable alternative to other scientific records (Tiago et al., 2017). Oriental Pied-Hornbills are morphologically conspicuous and loud, and because high human population density correlates to sampling density (Prudic et al., 2017), hornbills in Singapore are a suitable object for citizen science studies. This affords us the opportunity to use citizen science data to model where hornbills occur.
Here, we use data from citizen science platforms to model the occurrence of Oriental Pied-Hornbills as a function of land-use variables in Singapore. We hypothesize hornbills will thrive within grids with certain environmental features, and that these features should therefore be considered in conserving Oriental Pied-Hornbills, especially in urban environments. We then compare these qualitative features to Oriental Pied-Hornbill sightings in the region.
## 2. Materials and methods
We utilized the citizen science platforms, iNaturalist (www.inaturalist.org/) and eBird (ebird.org), and downloaded records of oriental hornbill sightings with spatial information from within Singapore. We excluded specific areas and data due to inaccessibility, such as islands and the ocean (Fig. 1). Data from eBird (https://doi.org/10.15468/dl.pdf5eq) for Oriental Pied-Hornbills for the selected areas of Singapore (downloaded on August 31, 2022) yielded 5195 approved observations from the eBird Basic Dataset (eBird Basic Dataset, 2022) from 1 January 2010–31 July 2022. We downloaded 1089 research-grade sightings from iNaturalist using the query ‘species = Anthracoceros albirostris, location = Singapore’, from September 2011 to August 2022, from most parts of Singapore, on August 24, 2022 (Fig. 1).

  1. Download: Download high-res image (427KB)
  2. Download: Download full-size image


Fig. 1. Map of selected study area of selected 3.0 km grids including Sentosa, excluding the Southern Islands and Bukom island.
We obtained geographical coordinates of sightings from the metadata of each sighting in the downloaded raw data and used those to map sightings on ArcGIS Pro 3.1.1 (www.esri.com). For land cover data, we included the high-resolution map by Gaw et al. (2019), loaded as a base map of Singapore’s national ecosystem cover. ArcGIS Pro 3.1.1 was used as the software to convert the raster map to polygon. The Coordinate Reference Systems used was the localized datum SVY21, commonly used in Singapore (SiReNT, 2020).
An earlier study performing generalized linear models (GLM) using a 2014 map made public by the Singapore Urban Redevelopment Authority (URA; https://www.ura.gov.sg/Corporate) revealed that a grid size of 2.5 km produced the best models (AIC = 199.7; BIC = 219.6; all other grid sizes produced models with AIC > 289.7; BIC > 311.1; Yahya, 2023). In the current analysis, we limited our analysis to 2 km and 3 km square grids, generated as shapefiles and layered onto the Gaw et al. (2019) map in ArcGIS. We obtained a list of spatial features in each grid by using the union tool in ArcGIS pro followed by the spatial join tool with the option _join one to one_ to record sightings. The bounding area of map was defined by selecting the grids with the Select function on ArcGIS, followed with removal of grids made up entirely of sea, or inaccessible areas such as the military sites.
For each grid square we calculated the percentage land-use of the total area, as determined by the Gaw et al. (2019) map, which lists thirteen land-use notations (Table A1). To facilitate a simpler yet robust ecosystem cover, we combined some land-use types into variables “built-up”, “water”, and combined freshwater marshes and freshwater swamp forests into “marsh” because these constituted a total of only 0.4 % of Singapore’s total area (Table A1).
We constructed GLM for grid sizes 2.0 km and 3.0 km with binomial error distribution (McCullagh and Nelder, 1989) in R Studio version 2023.06.0 (R Development Core Team, 2023), where sighting was a binary response variable, i.e., we did not include the number of sightings within a grid. We initially included the ten land-use categories as main predictors, and interaction terms between three pairs of predictors (Table 1). We enhanced model performance with stepwise logistic regression by iterative deletion of predictors based on statistical significance (Kassambara, 2018). We chose the candidate model with the lowest AIC and BIC (Burnham and Anderson, 2002). We predicted marginal effects of the selected model with other effects held constant at their mean values using the R package _sjPlot_ with the function plot_model (Lüdecke, 2023).
Table 1. Initial main and interaction effects for GLM, before stepwise deletion of effects.
**Main Effects** | **Interaction Effects**  
---|---  
Builtup | Builtup:Marsh  
Mangrove | Builtup:Vegetation with No Canopy  
Marsh | Marsh:Vegetation with No Canopy  
Pervious |   
Sea  
Vegetation with Canopy  
Vegetation with No Canopy  
Vegetation with Structure with Canopy |   
Vegetation with Structure without Canopy  
Water  
## 3. Results
After stepwise deletion of non-significant predictors (Table B1), both optimized GLM for 2.0 km and 3.0 km grid size contained similar significant predictors and neither included any significant interaction terms. For either grid size, percentages of land that were built-up, marsh, or vegetation without canopy were significant predictors of hornbill sightings (Table 2). The 3.0 km grid sized produced the lowest AIC (141.37) and BIC (153.36), values less than half those of the 2.0 km grid size (Table 2). We therefore consider the 3.0 km grid size for the rest of our analysis (Burnham and Anderson, 2002).
Table 2. Optimized final models for probability in hornbill sighting as response variable for the grid scale of 2.0 km, and 3.0 km squares with predictor variables.
**Model** | **Explanatory Variables** | **AIC** | **BIC** | **Estimate** | **Standard Error** | **Pr( >|z|)**  
---|---|---|---|---|---|---  
**Null Model (2 km)** | No variables | 415.96 | 419.74 | −0.64 | 0.12 | 5.54e−08***  
**2 km** |  | 308.44 | 323.53 |  |  |   
Empty Cell | Intercept |  |  | −2.50 | 0.29 | 2e−16***  
Empty Cell | Built-up |  |  | 3.03 | 0.81 | 0.000175 ***  
Empty Cell | Vegetation without canopy |  |  | 16.24 | 2.28 | 9.49e−13***  
Empty Cell | Marsh |  |  | 9.80 | 4.60 | 0.033 **  
**Null Model (3 km)** | No variables | 206.74 | 209.74 | −0.11 | 0.16 | 0.511  
**3 km** |  | 141.37 | 153.36 |  |  |   
Empty Cell | Intercept |  |  | −2.31 | 0.41 | 1.51e−08***  
Empty Cell | Built-up |  |  | 5.52 | 1.48 | 0.000199 ***  
Empty Cell | Vegetation without canopy |  |  | 17.42 | 4.31 | 5.24e−05***  
Empty Cell | Marsh |  |  | 21.21 | 10.17 | 0.037072*  
We summarized statistics of grids with and without sightings (Table B2). Hornbills were sighted in grids with higher percentages of most land-uses except sea. Interestingly, grids with hornbill sightings had, on average, about twice the percentages of built-up land-use (26.85 %), vegetation without canopy (10.50 %), and marsh cover (0.92 %), as grids without sightings (10.95 %; 5.02 %, and 0.50 %, respectively; Table B2).
Predicted marginal probabilities of hornbill sightings were positively related to all three significant land-use predictors (Fig. 2). All else being equal, probability of hornbill sighting rose fairly steadily with percent built-up cover (Fig. 2a). The probability of hornbill sightings also rose from roughly 25 % to more than 90 % as percent vegetation without canopy rose to roughly 50 % (Fig. 2b). The strongest effect was due to marsh cover, which increased the probability of hornbill sighting from roughly 50 % to 100 % as marsh cover rose to about 25 % (Fig. 2c).

  1. Download: Download high-res image (130KB)
  2. Download: Download full-size image


Fig. 2. Marginal relationships between the predicted probability of hornbill sightings and land use for (a) built-up; (b) vegetation without canopy; and (c) marsh. Curves derived from GLM model for 3.0 km grids (Table 2); shaded regions show 95 % confidence intervals around each curve. X-axes constrained to observed values with hornbill sightings.
## 4. Discussion
Our presence-only data, derived from citizen science observations, reveal factors in land use that predict occurrence of Oriental Pied-Hornbills. Overall, the percentages of built-up land, vegetation without canopy, and marsh cover within 3.0 km grids were positive predictors of the sighting of Oriental Pied-Hornbills in Singapore. These findings largely agree with published Oriental Pied-Hornbills’ habitat criteria (Kemp, 1995). Oriental Pied-Hornbills tend to live at forest edges, near coastal mangroves and other waterways, and on forested islands (Ng et al., 2011). Vegetation without canopy and marsh cover are likely near forest edges and waterways. However, we found that percent built-up land-use was also positively related hornbill sightings. In fact, the percentage of built-up area was twice a high in grids with hornbill sightings as in grids without sightings. The map we used to categorize land use (Gaw et al., 2019) does not include beach habitat. An earlier study (Yahya, 2023) found that beach cover was also a strong predictor of hornbill sightings. That positive relationship may also be due to hornbills living in coastal lowlands, where beaches are nearby.
One explanation for these patterns is sampling bias. People frequent open areas like parks with little canopy cover and areas near marshes or beaches. Hornbills are easy to see and identify. Frequent sightings in built-up areas might also indicate a sampling bias where there are more people. Studies with small samples often suffer from observation bias (Pearson et al., 2006). However, both Singapore’s built-up areas and nature reserves are frequently visited by birdwatchers and other nature observers. Because our study occurred in a country where many citizen and community scientists could contribute observations (Lloyd et al., 2020, Hall et al., 2021), we were able to include over 6000 records. We also limited our study to the occurrence, rather than the frequency, of hornbill sightings. These approaches should have reduced more egregious sampling biases.
Alternatively, Oriental Pied-Hornbills could genuinely be tolerant of human disturbance. The positive relationships we found between relatively open and built-up areas and hornbill sightings could reflect the ease with which hornbills have taken to living in Singapore. Anecdotal evidence supports this latter explanation. People in Singapore regularly see hornbills in housing estates and near blocks of flats – or perched on rooftops and balconies. Some facets of living in Singapore may make hornbills’ lives easier, including the cultivated fruit (Lok et al., 2013, Tan, 2010), and the ease with which they find other birds’ nestlings to eat (Loong et al., 2021). There may be fewer large avian predators that prey on Oriental Pied-Hornbills in Singapore compared to less urban areas as well.
We can compare the distribution of Oriental Pied-Hornbill sightings regionwide on iNaturalist to the patterns we found in Singapore. We focus on three sites: Langkawi, Peninsular Malaysia; Miri, Eastern Malaysia; and Brunei. We used all observations as of October 05, 2023 (Fig. 3). In Langkawi, sightings were abundant on the three beaches, along lowland coastal areas, and a few sightings (n = 4) were in the Wildlife Park in the center of the island (Fig. 3a). We found similar patterns in Miri, Malaysia, and in Brunei, where almost all sightings were near coasts and beaches (Fig. 3b). On a larger scale in Peninsular Malaysia, almost all sightings are in coastal regions. Inland sightings are generally along waterways and other wetlands, in low forests, and typically less than 50 m elevation (Fig. 3c). We cannot ascertain from these iNaturalist maps the degree of canopy cover, but sightings near beaches suggest that Oriental Pied-Hornbills often live in relatively open, low areas outside of Singapore, too. Wee et al. (2024) found a similar pattern, where MaxEnt models predicted the highest probabilities of Oriental Pied-Hornbill occurrences along the coasts of Sarawak or north of Loagan Bunut National Park (elevation 36 m) near Long Lama (see Fig. A.4 in Wee et al., 2024).

  1. Download: Download high-res image (90KB)
  2. Download: Download full-size image


Fig. 3. Maps of all records of Oriental Pied-Hornbill observations on iNaturalist in (a) Langkawi, Malaysia; (b) the west coast of Sarawak and Brunei; (c) Peninsular Malaysia. Red markings indicate research grade observations.
Identifying land-use features that allow hornbills to thrive can facilitate developing guiding principles in selecting a conservation area. Piasau Nature Reserve in Malaysia (https://piasaunaturereserve.com.my) may be one such successful case. Piasau was formerly a residential area for oil industry workers, and its vegetation includes inland coastal forest and sandy beach vegetation. Located at the beach near Miri River and 5 km north of Miri City, it was planned as a tourist resort (Konijnendijk, 2018). However, because of the presence of a breeding pair of Oriental Pied-Hornbills, it was converted into a nature park to facilitate Oriental Pied-Hornbill conservation. As a former residential area, much of Piasau is built up, and parts have vegetation without canopy.
The century-plus disappearance of Oriental Pied-Hornbills demonstrated that intense urbanization could drive this species locally extinct. However, while still near threatened in Singapore, their return shows that they are resilient and can thrive in an urban environment. The patterns we describe highlight the importance of urban land-use in conservation and management plans for Oriental Pied-Hornbills. For example, if Oriental Pied-Hornbills live in open vegetative habitat, near marshy areas or other wetlands, and are often seen near beaches (Yahya, 2023), then nesting boxes near those areas should be particularly effective.
## 5. Conclusion
We describe a model that estimates land-use that predicts the probability of Oriental Pied-Hornbill sightings. Percent built-up, marsh, and vegetation without canopy, are positively associated with hornbill sightings. Oriental Pied-Hornbills outside of Singapore are often found near water and beach habitat, and in very low elevation forests (e.g., Fig. 3), which is broadly consistent with our findings. The positive relationship between built-up land use and hornbill sightings shows that Oriental Pied-Hornbills at the very least tolerate urban environments. Our analysis demonstrates that citizen science data can be valuable in predicting species occurrence, especially in urban environments with lots of participants. Conservation managers can use similar analyses for predicting land-use important to other urban wildlife. Our study will also assist conservation managers in land-scarce Singapore where there are many competing land uses.
## Ethical approval
This study was purely observational; animals were not handled, manipulated, or fed in any way. Many of the observations were carried out by community scientists in Singapore.
## Declaration of Competing Interest
The authors have no competing financial or non-financial interests that are directly or indirectly related to this study.
## Acknowledgements
We would like to thank the citizen scientists of Singapore who have contributed to the eBird and iNaturalist databases. Portions of this study were conducted by Zaheedah in partial fulfilment of MSC requirements for BCNBCS, DBS, NUS. Ms Michelle Quak Song Yun from NUS Libraries has been very helpful in assisting with GIS, Dr Ian Zhi Wen Chan from Department of Biological Sciences, NUS for assistance on data analysis, and Ms Bee Choo Strange from Hornbill Research Foundation who provided insights to this study. The work was partly supported in part by the Singapore Ministry of Education through the Yale-NUS College grant R-607-265-226-121, and by Yale-NUS College Centre for International and Professional Experience (CIPE).
## Appendix A. Supplementary material
Download all supplementary files included with this article What’s this?
Download: Download Word document (14KB)
Supplementary material
Download: Download Word document (20KB)
Supplementary material
Special issue articlesRecommended articles
## Research data for this article

Global Biodiversity Information Facility
Biodiversity data
Data associated with the article:
Occurrence Download
Further information on research data
## References
  1. Brook et al., 2003
B.W. Brook, N.S. Sodhi, P.K. Ng
Catastrophic extinctions follow deforestation in Singapore
Nature, 424 (6947) (2003), pp. 420-423, 10.1038/nature01795
View in ScopusGoogle Scholar
  2. Burnham and Anderson, 2002
K.P. Burnham, D.R. Anderson
Model selection and multimodel inference: a practical information-theoretic approach
Springer Science & Business Media, New York (2002), 10.1007/b97636
Google Scholar
  3. Chisholm et al., 2023
R.A. Chisholm, N.P. Kristensen, F.E. Rheindt, Y.C. Kwek, J.S. Ascher, K.K.P. Lim, P.K.L. Ng, D.C.J. Yeo, R. Meier, H.H. Tan, X. Giam, Y.S. Yeoh, W.W. Seah, L.M. Berman, H.Z. Tan, K.R. Sadanandan, M. Theng, W.F.A. Jusoh, A. Jain, B. Huertas, D.J.X. Tan, A.C.R. Ng, A. Teo, Z. Yiwen, T.J.Y. Cho, Y.C.K. Sin
Two centuries of biodiversity discovery and loss in Singapore
Proc. Natl. Acad. Sci., _120_ (51) (2023), 10.1073/pnas.2309034120
Google Scholar
  4. Corlett, 1992
R.T. Corlett
The ecological transformation of Singapore, 1819-1990
J. Biogeogr., 19 (4) (1992), p. 411, 10.2307/2845569
View in ScopusGoogle Scholar
  5. Cremades and Ng, 2012
M. Cremades, S.C. Ng
Hornbills in the city: a conservation approach to hornbill study in Singapore
Natl. Parks Board Singap. (2012)
Google Scholar
  6. Cremades et al., 2011
M. Cremades, H.L.T. Wong, S. Koh, R. Segran, S. Ng
Re-introduction of the Oriental Pied Hornbill in Singapore, with emphasis on artificial nests
Raffles Bull. Zool., Supplement No. 24 (2011), pp. 5-10
Google Scholar
  7. De Bruyn et al., 2014
M. De Bruyn, B. Stelbrink, R.J. Morley, R. Hall, G.R. Carvalho, C.H. Cannon, G. Van den Bergh, E. Meijaard, I. Metcalfe, L. Boitani, L. Maiorano, R. Shoup, T. Von Rintelen
Borneo and Indochina are major evolutionary hotspots for Southeast Asian biodiversity
Syst. Biol., _63_ (6) (2014), pp. 879-901, 10.1093/sysbio/syu047
View in ScopusGoogle Scholar
  8. eBird Basic Dataset, 2022
eBird Basic Dataset
Version: EBD_relJul-2022
(Jul)
Cornell Lab of Ornithology, Ithaca, New York (2022), 10.15468/dl.pdf5eq
Google Scholar
  9. Gaw et al., 2019
L.Y.F. Gaw, A.T.K. Yee, D.R. Richards
A high-resolution map of Singapore’s terrestrial ecosystems
Data, 4 (3) (2019), p. 116, 10.3390/data4030116
View in ScopusGoogle Scholar
  10. Gibson-Hill, 1949
Gibson-Hill, C.A. (1949). A checklist of birds of Singapore island.
Google Scholar.%20A%20checklist%20of%20birds%20of%20Singapore%20island.)
  11. Hall et al., 2021
M.J. Hall, J.M. Martin, A.L. Burns, D.F. Hochuli
Ecological insights into a charismatic bird using different citizen science approaches
Austral Ecol., _46_ (8) (2021), pp. 1255-1265, 10.1111/aec.13062
View in ScopusGoogle Scholar
  12. Hughes, 2017
A.C. Hughes
Understanding the drivers of Southeast Asian biodiversity loss
10/1002/ecs2.1624
Ecosphere, 8 (1) (2017), Article e01624, 10.1002/ecs2.1624
Google Scholar
  13. Kassambara, 2018
Kassambara, A. (2018). Machine learning essentials: Practical guide in R _. STHDA_ .
Google Scholar.%20Machine%20learning%20essentials%3A%20Practical%20guide%20in%20R.%20STHDA%20.)
  14. Kemp, 1995
A. Kemp
The hornbills: Bucerotidae
Oxford University Press, Oxford (1995), p. 302
CrossrefGoogle Scholar
  15. Konijnendijk, 2018
C.C. Konijnendijk
The forest and the city: The cultural landscape of urban woodland
Springer (2018), 10.1007/978-3-319-75076-7
Google Scholar
  16. Lloyd et al., 2020
T.J. Lloyd, R.A. Fuller, J.L. Oliver, A.I. Tulloch, M. Barnes, R. Steven
Estimating the spatial coverage of citizen science for monitoring threatened species
Glob. Ecol. Conserv., _23_ (2020), Article e01048, 10.1016/j.gecco.2020.e01048
View PDFView articleView in ScopusGoogle Scholar
  17. Lok et al., 2013
A.F. Lok, W.F. Ang, B.Y.Q. Ng, T.M. Leong, C.K. Yeo, H.T.W. Tan
Native fig species as a keystone resource for the singapore urban environment
Raffles Mus. Biodivers. (2013)
(Singapore)
Google Scholar
  18. Loong et al., 2021
S. Loong, C.K.S. Yong, P. Johns, T. Plowden, D.L. Yong, J. Lee, A. Jain
Nest predation by oriental pied hornbills (_Anthracoceros albirostris_) in Singapore
Bird. ASIA, 35 (2021), pp. 86-91
Google Scholar
  19. Lüdecke, 2023
Lüdecke D. (2023). sjPlot: Data Visualization for Statistics in Social Science. R package version 2.8.15. 〈https://CRAN.R-project.org/package=sjPlot〉.
Google Scholar.%20sjPlot%3A%20Data%20Visualization%20for%20Statistics%20in%20Social%20Science.%20R%20package%20version%202.8.15.%20%E3%80%88https%3A%2F%2FCRAN.R-project.org%2Fpackage%3DsjPlot%E3%80%89.)
  20. Marsden and Pilgrim, 2002
S.J. Marsden, J.D. Pilgrim
Factors influencing the abundance of parrots and hornbills in pristine and disturbed forests on New Britain, PNG
Ibis, _145_ (1) (2002), pp. 45-53, 10.1046/j.1474-919x.2003.00107.x
Google Scholar
  21. McCullagh and Nelder, 1989
P. McCullagh, J.A. Nelder
Generalized Linear Models
Chapman Hall (1989)
Google Scholar
  22. Miller, 2010
J. Miller
Species distribution modeling
Geogr. Compass, _4_ (6) (2010), pp. 490-509, 10.1111/j.1749-8198.2010.00351.x
View in ScopusGoogle Scholar
  23. Ng et al., 2011
S. Ng, H. Lai, M. Cremades, M.T. Lim, S. Mohammed Tali
Breeding observations on the Oriental Pied Hornbill in nest cavities and in artificial nests in Singapore, with emphasis on infanticide-cannibalism
Raffles Bull. Zool. Suppl., 24 (2011), pp. 15-22
Google Scholar
  24. Pearson et al., 2006
R.G. Pearson, C.J. Raxworthy, M. Nakamura, A. Townsend Peterson
Predicting species distributions from small numbers of occurrence records: a test case using cryptic geckos in Madagascar
J. Biogeogr., 34 (1) (2006), pp. 102-117, 10.1111/j.1365-2699.2006.01594.x
Google Scholar
  25. Prudic et al., 2017
K. Prudic, K. McFarland, J. Oliver, R. Hutchinson, E. Long, J. Kerr, M. Larrivée
EButterfly: Leveraging massive online citizen science for butterfly conservation
Insects, 8 (2) (2017), p. 53, 10.3390/insects8020053
View in ScopusGoogle Scholar
  26. R Development Core Team, 2023
R Development Core Team
R: A language and environment for statistical computing
R Foundation for Statistical Computing, Vienna (2023)
〈https://www.R-project.org〉
Google Scholar
  27. SiReNT, 2020
SiReNT - Singapore satellite positioning reference network - Plane coordinate system - SVY21. (2020, June 8). 〈https://app.sla.gov.sg/sirent/About/PlaneCoordinateSystem〉.
Google Scholar.%20%E3%80%88https%3A%2F%2Fapp.sla.gov.sg%2Fsirent%2FAbout%2FPlaneCoordinateSystem%E3%80%89.)
  28. Strange and O’Dempsey, 2022
B.C. Strange, T. O’Dempsey
A note on oriental pied hornbill reintroduction in Singapore and its dispersal from 2010-2021
Hornbill Nat. Hist. Conserv., Vol. 3 (2022), pp. 28-31
〈https://iucnhornbills.org/wp-content/uploads/2022/07/HNHC_3_Strange-and-ODempsey.pdf〉
2022
Google Scholar
  29. Sullivan et al., 2009
B.L. Sullivan, C.L. Wood, M.J. Iliff, R.E. Bonney, D. Fink, S. Kelling
EBird: a citizen-based bird observation network in the biological sciences
Biol. Conserv., _142_ (10) (2009), pp. 2282-2292, 10.1016/j.biocon.2009.05.006
View PDFView articleView in ScopusGoogle Scholar
  30. Tan, 2010
H.H. Tan
Spider-feeding behaviour of the oriental pied hornbill
Nat. Singap., 3 (2010), pp. 283-286
CrossrefGoogle Scholar
  31. Tiago et al., 2017
P. Tiago, H.M. Pereira, C. Capinha
Using citizen science data to estimate climatic niches and species distributions
Basic Appl. Ecol., 20 (2017), pp. 75-85, 10.1016/j.baae.2017.04.001
View PDFView articleView in ScopusGoogle Scholar
  32. Trisurat et al., 2013
Y. Trisurat, V. Chimchome, A. Pattanavibool, S. Jinamoy, S. Thongaree, B. Kanchanasakha, S. Simcharoen, K. Sribuarod, N. Mahannop, P. Poonswad
An assessment of the distribution and conservation status of hornbill species in Thailand
Oryx, _47_ (3) (2013), pp. 441-450, 10.1017/s0030605311001128
View in ScopusGoogle Scholar
  33. URA,
URA). 〈https://www.ura.gov.sg/-/media/Corporate/Planning/Master-Plan/MP19writtenstatement.pdf〉.
Google Scholar.%20%E3%80%88https%3A%2F%2Fwww.ura.gov.sg%2F-%2Fmedia%2FCorporate%2FPlanning%2FMaster-Plan%2FMP19writtenstatement.pdf%E3%80%89.)
  34. Wee et al., 2024
S.Q.W. Wee, J.J.H. Teo, B. Teepol, H.N.I. Jelembai, N.J. Au, C.A. Yeap, A. Jain
Identifying important hornbill landscapes in Sarawak, Malaysia
Glob. Ecol. Conserv., 50 (2024), Article e02828
〈https://doi-org.libproxy1.nus.edu.sg/10.1016/j.gecco.2024.e02828〉
View PDFView articleView in ScopusGoogle Scholar
  35. Wong, 2011
T.W. Wong
The Singapore Hornbill project: a great but simple idea
Raffles Bull. Zool., Supplement No. 24 (2011), pp. 3-4
View in ScopusGoogle Scholar
  36. Yahya, 2023
Z. Yahya
Land use and oriental pied hornbill occurrence in Singapore
(MSc Thesis)
Department of Biological Sciences, National University of Singapore (2023)
Google Scholar


## Cited by (0) 

1
    
ORCID ID: 0000-0003-2301-0212
© 2024 The Authors. Published by Elsevier B.V.
## Part of special issue
Hornbill ecology and conservation in times of global change
Edited by Aparajita Datta, Rohit Naniwadekar, Lisa Nupen
View special issue
## Recommended articles
  * ### Multiple housing problems: A view through the housing niche lens
Cities, Volume 62, 2017, pp. 146-151
Emma Baker, Laurence Lester
View PDF
  * ### Crocodiles of the Ouémé lower valley in Southern Benin: Local perceptions, uses and conservation challenges
Global Ecology and Conservation, Volume 54, 2024, Article e03172
Obakèmi Jean-Pierre Olofindji
View PDF
  * ### _Tilia_ trees are preferred hosts of several ectomycorrhizal Ascomycota – New insights supported by the first community study of the endemic _Tilia kiusiana_
Global Ecology and Conservation, Volume 54, 2024, Article e03187
Daniel Janowski, Kazuhide Nara
View PDF
  * ### Distribution status and influence of climate change on patterns of distribution of hornbills in Sri Lanka
Global Ecology and Conservation, Volume 51, 2024, Article e02903
Iresha L. Wijerathne, …, Sriyani Wickramasinghe
View PDF
  * ### Variation patterns in foliar δ13C and δ15N among plant life types along an altitudinal gradient on the Tibetan Plateau
Global Ecology and Conservation, Volume 54, 2024, Article e03188
Ribu Shama, …, Almaz Borjigidai
View PDF
  * ### Modelling and mapping the abundance of lingonberry (_Vaccinium vitis-idaea_ L.) in Norway
Global Ecology and Conservation, Volume 54, 2024, Article e03195
Jari Miina, …, Inger Martinussen
View PDF


Show 3 more articles
## Article Metrics
### Captures
  * Mendeley Readers8


### Mentions
  * News Mentions1


View details

  * About ScienceDirect
  * Remote access
  * Contact and support
  * Terms and conditions
  * Privacy policy


Cookies are used by this site. **Cookie Settings**
All content on this site: Copyright © 2025 Elsevier B.V., its licensors, and contributors. All rights are reserved, including those for text and data mining, AI training, and similar technologies. For all open access content, the relevant licensing terms apply.