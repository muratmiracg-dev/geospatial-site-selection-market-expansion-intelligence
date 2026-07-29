"""Deterministic reference locations for the fictional MarmaraMart chain."""

from __future__ import annotations

DISTRICT_ANCHORS = [
    ("Beyoglu", 41.0369, 28.9850, 1.00, 0.97, 0.98),
    ("Sisli", 41.0602, 28.9877, 1.00, 1.00, 0.98),
    ("Besiktas", 41.0430, 29.0094, 0.96, 1.00, 0.97),
    ("Levent", 41.0814, 29.0120, 0.93, 1.00, 0.98),
    ("Bakirkoy", 40.9819, 28.8721, 0.90, 0.88, 0.91),
    ("Bahcelievler", 41.0000, 28.8590, 0.95, 0.73, 0.83),
    ("Kagithane", 41.0810, 28.9700, 0.92, 0.75, 0.82),
    ("Basaksehir", 41.1075, 28.8065, 0.78, 0.72, 0.74),
    ("Beylikduzu", 41.0010, 28.6410, 0.83, 0.75, 0.72),
    ("Esenyurt", 41.0340, 28.6800, 1.00, 0.55, 0.66),
    ("Kadikoy", 40.9906, 29.0288, 1.00, 0.95, 0.98),
    ("Uskudar", 41.0256, 29.0153, 0.91, 0.84, 0.91),
    ("Atasehir", 40.9923, 29.1244, 0.92, 0.94, 0.91),
    ("Umraniye", 41.0164, 29.1248, 0.97, 0.71, 0.81),
    ("Maltepe", 40.9357, 29.1551, 0.91, 0.73, 0.79),
    ("Kartal", 40.8897, 29.1856, 0.85, 0.69, 0.75),
    ("Pendik", 40.8775, 29.2724, 0.83, 0.65, 0.70),
    ("Sancaktepe", 41.0020, 29.2310, 0.80, 0.57, 0.65),
]

CANDIDATE_LOCATIONS = [
    ("C01", "Bahcelievler Metro", 41.0031, 28.8628),
    ("C02", "Beylikduzu Marina", 40.9814, 28.6417),
    ("C03", "Avcilar University", 40.9872, 28.7235),
    ("C04", "Esenyurt Square", 41.0349, 28.6804),
    ("C05", "Kagithane Axis", 41.0858, 28.9726),
    ("C06", "Basaksehir Center", 41.1068, 28.8061),
    ("C07", "Eyupsultan Hub", 41.0757, 28.9336),
    ("C08", "Sariyer Corridor", 41.1662, 29.0500),
    ("C09", "Zeytinburnu Transit", 40.9938, 28.9057),
    ("C10", "Bayrampasa Forum", 41.0462, 28.8965),
    ("C11", "Atasehir Finance", 40.9904, 29.1275),
    ("C12", "Umraniye Center", 41.0236, 29.1187),
    ("C13", "Maltepe Coastal", 40.9217, 29.1433),
    ("C14", "Kartal Junction", 40.8972, 29.1915),
    ("C15", "Pendik Marina", 40.8758, 29.2336),
    ("C16", "Cekmekoy Center", 41.0331, 29.1784),
    ("C17", "Sancaktepe Hub", 41.0026, 29.2317),
    ("C18", "Sultanbeyli Square", 40.9684, 29.2708),
    ("C19", "Tuzla Technology", 40.8289, 29.3185),
    ("C20", "Buyukcekmece Center", 41.0201, 28.5850),
    ("C21", "Arnavutkoy Center", 41.1864, 28.7380),
    ("C22", "Silivri Gateway", 41.0730, 28.2478),
    ("C23", "Gokturk Center", 41.1778, 28.8895),
    ("C24", "Ikitelli Industry", 41.0790, 28.7985),
]

EXISTING_STORES = [
    ("S01", "Besiktas", 41.0433, 29.0059, 620),
    ("S02", "Sisli", 41.0610, 28.9870, 650),
    ("S03", "Levent", 41.0795, 29.0125, 720),
    ("S04", "Taksim", 41.0370, 28.9850, 540),
    ("S05", "Bakirkoy", 40.9815, 28.8725, 680),
    ("S06", "Kadikoy", 40.9907, 29.0277, 700),
    ("S07", "Uskudar", 41.0262, 29.0160, 610),
    ("S08", "Atasehir", 40.9920, 29.1245, 760),
    ("S09", "Maltepe", 40.9363, 29.1545, 690),
    ("S10", "Umraniye", 41.0168, 29.1240, 710),
]

BRIDGE_CONNECTIONS = [
    ((41.0454, 29.0341), (41.0448, 29.0400), "15_July_Martyrs"),
    ((41.0900, 29.0580), (41.0905, 29.0740), "Fatih_Sultan_Mehmet"),
    ((41.2020, 29.1000), (41.2030, 29.1180), "Yavuz_Sultan_Selim"),
]
