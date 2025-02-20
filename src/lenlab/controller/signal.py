sine_table = [  # frequency_hertz, interval_25ns, points
    (100, 200, 2000),
    (102, 200, 1954),
    (105, 200, 1910),
    (107, 200, 1866),
    (110, 200, 1824),
    (112, 200, 1782),
    (115, 200, 1742),
    (118, 200, 1702),
    (120, 200, 1664),
    (123, 200, 1626),
    (126, 200, 1588),
    (129, 200, 1552),
    (132, 200, 1518),
    (135, 200, 1482),
    (138, 200, 1448),
    (141, 200, 1416),
    (145, 200, 1384),
    (148, 200, 1352),
    (151, 200, 1322),
    (155, 200, 1292),
    (158, 200, 1262),
    (162, 200, 1234),
    (166, 200, 1206),
    (170, 200, 1178),
    (174, 200, 1150),
    (178, 200, 1124),
    (182, 200, 1100),
    (186, 200, 1074),
    (190, 200, 1050),
    (195, 200, 1026),
    (200, 200, 1002),
    (204, 200, 980),
    (209, 200, 958),
    (214, 200, 936),
    (219, 200, 914),
    (224, 200, 894),
    (229, 200, 874),
    (234, 200, 854),
    (240, 200, 834),
    (246, 200, 814),
    (251, 80, 1990),
    (257, 80, 1946),
    (263, 80, 1900),
    (269, 80, 1858),
    (275, 80, 1816),
    (282, 80, 1774),
    (288, 80, 1734),
    (295, 80, 1694),
    (302, 80, 1656),
    (309, 80, 1618),
    (316, 80, 1582),
    (323, 80, 1546),
    (331, 80, 1510),
    (339, 80, 1476),
    (347, 80, 1442),
    (355, 80, 1410),
    (363, 80, 1378),
    (371, 80, 1346),
    (380, 80, 1316),
    (389, 80, 1286),
    (398, 80, 1256),
    (407, 80, 1228),
    (417, 80, 1200),
    (427, 80, 1172),
    (436, 80, 1146),
    (446, 80, 1120),
    (457, 80, 1094),
    (468, 80, 1068),
    (479, 80, 1044),
    (490, 80, 1020),
    (501, 40, 1996),
    (513, 40, 1950),
    (525, 40, 1906),
    (537, 40, 1862),
    (549, 40, 1820),
    (562, 40, 1778),
    (575, 40, 1738),
    (589, 40, 1698),
    (602, 40, 1660),
    (617, 40, 1622),
    (631, 40, 1584),
    (646, 40, 1548),
    (661, 40, 1514),
    (676, 40, 1480),
    (692, 40, 1446),
    (708, 40, 1412),
    (725, 40, 1380),
    (742, 40, 1348),
    (759, 40, 1318),
    (776, 40, 1288),
    (795, 40, 1258),
    (813, 40, 1230),
    (832, 40, 1202),
    (852, 40, 1174),
    (871, 40, 1148),
    (891, 40, 1122),
    (912, 40, 1096),
    (933, 40, 1072),
    (954, 40, 1048),
    (977, 40, 1024),
    (1000, 40, 1000),
    (1022, 40, 978),
    (1048, 40, 954),
    (1071, 40, 934),
    (1096, 40, 912),
    (1121, 40, 892),
    (1149, 40, 870),
    (1174, 40, 852),
    (1202, 40, 832),
    (1232, 40, 812),
    (1259, 40, 794),
    (1289, 40, 776),
    (1319, 40, 758),
    (1348, 40, 742),
    (1381, 40, 724),
    (1412, 40, 708),
    (1445, 40, 692),
    (1479, 40, 676),
    (1515, 40, 660),
    (1548, 40, 646),
    (1587, 40, 630),
    (1623, 40, 616),
    (1661, 40, 602),
    (1701, 40, 588),
    (1736, 40, 576),
    (1779, 40, 562),
    (1818, 40, 550),
    (1859, 40, 538),
    (1908, 40, 524),
    (1953, 40, 512),
    (1992, 40, 502),
    (2041, 40, 490),
    (2092, 40, 478),
    (2137, 40, 468),
    (2183, 40, 458),
    (2242, 40, 446),
    (2294, 40, 436),
    (2347, 40, 426),
    (2404, 40, 416),
    (2451, 40, 408),
    (2513, 40, 398),
    (2564, 40, 390),
    (2632, 40, 380),
    (2688, 40, 372),
    (2747, 40, 364),
    (2825, 40, 354),
    (2890, 40, 346),
    (2959, 40, 338),
    (3012, 40, 332),
    (3086, 40, 324),
    (3165, 40, 316),
    (3226, 40, 310),
    (3311, 40, 302),
    (3378, 40, 296),
    (3472, 40, 288),
    (3546, 40, 282),
    (3623, 40, 276),
    (3704, 40, 270),
    (3788, 40, 264),
    (3876, 40, 258),
    (3968, 40, 252),
    (4065, 40, 246),
    (4167, 40, 240),
    (4274, 40, 234),
    (4348, 40, 230),
    (4464, 40, 224),
    (4587, 40, 218),
    (4673, 40, 214),
    (4808, 40, 208),
    (4902, 40, 204),
    (5000, 40, 200),
    (5155, 40, 194),
    (5263, 40, 190),
    (5376, 40, 186),
    (5495, 40, 182),
    (5618, 40, 178),
    (5747, 40, 174),
    (5882, 40, 170),
    (6024, 40, 166),
    (6173, 40, 162),
    (6329, 40, 158),
    (6494, 40, 154),
    (6579, 40, 152),
    (6757, 40, 148),
    (6944, 40, 144),
    (7042, 40, 142),
    (7246, 40, 138),
    (7463, 40, 134),
    (7576, 40, 132),
    (7812, 40, 128),
    (7937, 40, 126),
    (8065, 40, 124),
    (8333, 40, 120),
    (8475, 40, 118),
    (8772, 40, 114),
    (8929, 40, 112),
    (9091, 40, 110),
    (9259, 40, 108),
    (9615, 40, 104),
    (9804, 40, 102),
    (10000, 40, 100),
]
