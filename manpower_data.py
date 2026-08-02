"""
manpower_data.py
Pure data layer for the Manpower Allocation & Budget module - no GUI
imports at all (no Tkinter, no openpyxl), so this is safe to import on
Android via python-for-android. Same manpower_positions table/schema
and business logic as the desktop version in manpower_allocation.py -
only the presentation layer differs between the two.
"""

import os

import database as db

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "accounts_exports")

COMPANY_NAME = "Ranaya Silks"
COMPANY_ADDRESS = "48/26 Kamalr Street, Tiruchengode, Namakkal, TN-637211"

MAROON = "4E0000"
GOLD = "B8860B"
LIGHT_TINT = "FAF2F4"
FONT_NAME = "Calibri"

ALL_FLOORS = "All Floors"
ALL_DEPARTMENTS = "All Departments"

# Display order for floors (report order, not alphabetical)
FLOOR_ORDER = [
    "Ground Floor", "First Floor", "Second Floor", "Third Floor",
    "RSM (Jewellery)", "Backend Office", "Entrance",
]

# Display order for budget categories within a floor's breakdown table
CATEGORY_ORDER = [
    "Designation", "Designation Core 1", "Designation Core 2",
    "Counter Incharge (A+)", "Sales (A)", "Sales (B)", "Sales (C)",
    "Cash Team", "Part Time",
    "EDP & Entry", "Jewel EDP & Data Entry", "HR Dep", "Online Dep", "Editing Dep",
    "Welcome Staff", "Building Maintenance", "Security", "Vehicle Handler",
    "Parking Incharge", "Night Security", "House Keeping",
]


def _cat_sort_key(cat):
    return CATEGORY_ORDER.index(cat) if cat in CATEGORY_ORDER else len(CATEGORY_ORDER)


def _floor_sort_key(floor):
    return FLOOR_ORDER.index(floor) if floor in FLOOR_ORDER else len(FLOOR_ORDER)


# =================================================================
# Seed data - transcribed from the printed report "as on 02/08/26"
# (floor, department, category, designation, staff_name, grade,
#  salary_package, gender). Blank staff_name = vacant seat.
# =================================================================

def _seed_rows():
    rows = []

    def add(floor, dept, cat, desig, name, grade, salary, gender):
        rows.append((floor, dept, cat, desig, name, grade, salary, gender))

    # ---------------- GROUND FLOOR ----------------
    F = "Ground Floor"
    add(F, "Floor Management", "Designation", "Floor Manager", "Poovarasan", "A+", 19000, "Male")
    add(F, "Petty Cash & Cashier", "Cash Team", "Petty Cash", "Sasi Kala", "A+", 11000, "Female")
    add(F, "Petty Cash & Cashier", "Cash Team", "Cashier (Ground-1)", "Srinivasan", "A+", 14000, "Male")
    add(F, "Petty Cash & Cashier", "Cash Team", "Cashier (Ground-2)", "yuvasri", "A+", 10000, "Female")
    add(F, "Eco Fancy & Syn Sarees", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 17000, "Male")
    add(F, "Eco Fancy & Syn Sarees", "Sales (A)", "Sales", "Latha", "A", 13000, "Female")
    add(F, "Eco Fancy & Syn Sarees", "Sales (A)", "Sales", "Sathyabhama", "A", 13000, "Female")
    add(F, "Eco Fancy & Syn Sarees", "Sales (B)", "Sales", "Meenatchi", "B", 11000, "Female")
    add(F, "Eco Fancy & Syn Sarees", "Sales (B)", "Sales", "", "B", 12000, "Male")
    add(F, "Eco Fancy & Syn Sarees", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Handloom & Fancy Cotton", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 17000, "Male")
    add(F, "Handloom & Fancy Cotton", "Sales (A)", "Sales", "Tamil Selvi", "A", 11000, "Female")
    add(F, "Handloom & Fancy Cotton", "Sales (A)", "Sales", "Gunasekaran", "A", 17000, "Male")
    add(F, "Handloom & Fancy Cotton", "Sales (B)", "Sales", "Sumathi", "B", 11000, "Female")
    add(F, "Handloom & Fancy Cotton", "Sales (B)", "Sales", "", "B", 9000, "Female")
    add(F, "Bin Section", "Sales (A)", "Bin Incharge", "Ramya", "A", 10500, "Female")
    add(F, "Bin Section", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Bin Section", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Nighty", "Counter Incharge (A+)", "Counter Incharge", "Gomathi", "A+", 13000, "Female")
    add(F, "Nighty", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Design Blouse - 44 Inch", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 16000, "Male")
    add(F, "Design Blouse - 36 Inch", "Sales (A)", "Sales", "Tamil Selvi", "A", 12500, "Female")
    add(F, "Inskirt & Falls", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 12000, "Female")
    add(F, "Inskirt & Falls", "Sales (C)", "Sales", "Dhivya Dharshini", "C", 10000, "Female")
    add(F, "Lining & Silk Cotton", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 12000, "Female")
    add(F, "Lining & Silk Cotton", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Full Voil Mtrs", "Counter Incharge (A+)", "Counter Incharge/AFM", "Raja Durai", "A+", 16000, "Male")
    add(F, "Full Voil Mtrs", "Sales (B)", "Sales", "Sasikala", "B", 9500, "Female")
    add(F, "Part Time Pool", "Part Time", "Sales", "Bharathi", "D", 8000, "Female")
    add(F, "Part Time Pool", "Part Time", "Sales", "Sumithra", "D", 8000, "Female")
    add(F, "Part Time Pool", "Part Time", "Sales", "", "D", 8000, "Male")
    add(F, "Part Time Pool", "Part Time", "Sales", "", "D", 8000, "Male")
    add(F, "Part Time Pool", "Part Time", "Sales", "Elakkiya", "D", 8000, "Female")
    add(F, "Part Time Pool", "Part Time", "Petty Cash", "Rabina", "D", 8000, "Female")
    add(F, "Part Time Pool", "Part Time", "Packing", "Dharshini", "D", 8000, "Male")

    # ---------------- FIRST FLOOR ----------------
    F = "First Floor"
    add(F, "Floor Management", "Designation", "Floor Manager", "Deepa", "A+", 15000, "Female")
    add(F, "Cashier", "Cash Team", "Cashier (Cash-1)", "Manikandan", "A+", 15000, "Male")
    add(F, "Cashier", "Cash Team", "Cashier (Cash-2)", "", "A+", 0, "Male")
    add(F, "Silk Sarees & Lehenga", "Counter Incharge (A+)", "Counter Incharge", "Raj Kumar", "A+", 18000, "Male")
    add(F, "Silk Sarees & Lehenga", "Sales (A)", "Sales", "", "A", 17000, "Male")
    add(F, "Silk Sarees & Lehenga", "Sales (A)", "Sales", "Menaga", "A", 13000, "Female")
    add(F, "Silk Sarees & Lehenga", "Sales (C)", "Sales", "", "C", 11000, "Female")
    add(F, "Fancy Sarees", "Counter Incharge (A+)", "Counter Incharge", "Ashok Kumar", "A+", 16000, "Male")
    add(F, "Fancy Sarees", "Sales (A)", "Sales", "", "A", 15000, "Male")
    add(F, "Fancy Sarees", "Sales (B)", "Sales", "Revathi", "B", 11000, "Female")
    add(F, "Fancy Sarees", "Sales (A)", "Sales", "Karthikeyan", "A", 16000, "Female")
    add(F, "Shirting & Suiting", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 14000, "Male")
    add(F, "Shirting & Suiting", "Sales (A)", "Sales", "Prakash", "A", 18000, "Male")
    add(F, "Shirting & Suiting", "Sales (A)", "Sales", "Murugan", "A", 18000, "Male")
    add(F, "Shirting & Suiting", "Sales (A)", "Sales", "Kavimaran", "A", 14000, "Male")
    add(F, "Chudi RM & Material", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 17000, "Male")
    add(F, "Chudi RM & Material", "Sales (A)", "Sales", "Vasavi", "A", 11000, "Female")
    add(F, "Chudi RM & Material", "Sales (B)", "Sales", "Sathya", "B", 11000, "Female")
    add(F, "Long Kurti", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 17000, "Male")
    add(F, "Long Kurti", "Sales (A)", "Sales", "Seethalakshmi", "A", 13000, "Female")
    add(F, "Long Kurti", "Sales (B)", "Sales", "Geetha", "B", 11500, "Female")
    add(F, "Long Kurti", "Sales (C)", "Sales", "Shanmuga Priya", "C", 11000, "Female")
    add(F, "Leggings & Shawl", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 12000, "Female")
    add(F, "Leggings & Shawl", "Sales (B)", "Sales", "", "B", 9500, "Female")
    add(F, "Womens Inner Wear", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 17000, "Female")
    add(F, "Womens Inner Wear", "Sales (A)", "Sales", "Mallika", "A", 12500, "Female")
    add(F, "Womens Inner Wear", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Bin Section", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Bin Section", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Part Time Pool", "Part Time", "Sales", "KAVINAYA", "D", 8000, "Female")
    add(F, "Part Time Pool", "Part Time", "Sales", "NITHYASRI", "D", 8000, "Female")
    add(F, "Part Time Pool", "Part Time", "Sales", "SARAN", "D", 8000, "Male")
    add(F, "Part Time Pool", "Part Time", "Sales", "RAGURAM", "D", 8000, "Female")
    add(F, "Part Time Pool", "Part Time", "Sales", "SURYA", "D", 8000, "Female")
    add(F, "Part Time Pool", "Part Time", "Sales", "", "D", 8000, "Male")
    add(F, "Part Time Pool", "Part Time", "Packing", "GOPIKA", "D", 8000, "Female")

    # ---------------- SECOND FLOOR ----------------
    F = "Second Floor"
    add(F, "Floor Management", "Designation", "Floor Manager", "Mathan Kumar", "A+", 17000, "Male")
    add(F, "Cashier", "Cash Team", "Cashier (Cash-1)", "Senthilkumar", "A+", 15000, "Male")
    add(F, "Cashier", "Cash Team", "Cashier (Cash-2)", "", "A+", 0, "Female")
    add(F, "New Born", "Counter Incharge (A+)", "Counter Incharge", "Renuga Devi", "A+", 10000, "Female")
    add(F, "Pattu Pavadai & Frock & Long Frock", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 15000, "Female")
    add(F, "Pattu Pavadai & Frock & Long Frock", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 17000, "Male")
    add(F, "Pattu Pavadai & Frock & Long Frock", "Sales (A)", "Sales", "Manikandan", "A", 15000, "Male")
    add(F, "Pattu Pavadai & Frock & Long Frock", "Sales (B)", "Sales", "Kalaivani", "B", 11500, "Female")
    add(F, "Pattu Pavadai & Frock & Long Frock", "Sales (B)", "Sales", "Kokila", "B", 9500, "Female")
    add(F, "Western", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 17000, "Male")
    add(F, "Western", "Sales (A)", "Sales", "", "A", 15000, "Male")
    add(F, "Western", "Sales (B)", "Sales", "Lingeswaran", "B", 13000, "Male")
    add(F, "Long Frock & Western", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Night Suit & Western", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 12000, "Female")
    add(F, "Night Suit & Western", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Night Suit & Western", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Boys Shirts", "Sales (A)", "Sales", "Deepika", "A", 12000, "Female")
    add(F, "Boys Shirts", "Sales (C)", "Sales", "", "C", 12000, "Male")
    add(F, "Boys Lounge Wear", "Sales (A)", "Sales", "Kayalvizhi", "A", 11000, "Female")
    add(F, "Boys Lounge Wear", "Sales (C)", "Sales", "", "C", 12000, "Male")
    add(F, "Pant Shirt & Babasuit", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 17000, "Male")
    add(F, "Boys Dhoti Set", "Sales (A)", "Sales", "Prabhakaran", "A", 14000, "Male")
    add(F, "Boys Dhoti Set", "Sales (B)", "Sales", "Praveen", "B", 12500, "Male")
    add(F, "Bin Section", "Sales (B)", "Sales", "Shanthi", "B", 12000, "Female")
    add(F, "Bin Section", "Sales (B)", "Sales", "Keerthana", "B", 10000, "Female")
    add(F, "Bin Section", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Mens Shirt", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 17000, "Male")
    add(F, "Mens Shirt", "Sales (A)", "Sales", "Kavitha", "A", 13000, "Female")
    add(F, "Mens Shirt", "Sales (C)", "Sales", "Santhosh", "C", 13000, "Male")
    add(F, "Mens Pant & Blazer", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 17000, "Male")
    add(F, "Mens Pant & Blazer", "Sales (A)", "Sales", "Murugan", "A", 16500, "Male")
    add(F, "Mens Pant & Blazer", "Sales (A)", "Sales", "Vanithraj", "A", 14000, "Male")
    add(F, "Mens Lounge Wear", "Sales (A)", "Sales", "Venkatachalam", "A", 17000, "Male")
    add(F, "Mens Lounge Wear", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Part Time Pool", "Part Time", "Sales", "Shalini", "D", 8000, "Female")
    add(F, "Part Time Pool", "Part Time", "Sales", "Amar", "D", 8000, "Male")
    add(F, "Part Time Pool", "Part Time", "Sales", "Guruprasath", "D", 8000, "Male")
    add(F, "Part Time Pool", "Part Time", "Sales", "Vishnu Jainth", "D", 8000, "Male")
    add(F, "Part Time Pool", "Part Time", "Sales", "", "D", 8000, "Male")
    add(F, "Part Time Pool", "Part Time", "Sales", "", "D", 8000, "Male")
    add(F, "Part Time Pool", "Part Time", "Packing", "", "D", 8000, "Male")

    # ---------------- THIRD FLOOR ----------------
    F = "Third Floor"
    add(F, "Floor Management", "Designation", "Floor Manager", "Saravanan", "A+", 14000, "Male")
    add(F, "Cashier", "Cash Team", "Cashier (Cash-1)", "Balaji", "A+", 14500, "Male")
    add(F, "Cashier", "Cash Team", "Cashier (Cash-2)", "", "A+", 0, "Male")
    add(F, "Steel Section", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 17000, "Male")
    add(F, "Steel Section", "Sales (A)", "Sales", "", "A", 13000, "Female")
    add(F, "Steel Section", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Plastic Section", "Counter Incharge (A+)", "Counter Incharge", "Rihana", "A+", 12000, "Female")
    add(F, "Plastic Section", "Sales (B)", "Sales", "", "B", 11000, "Female")
    add(F, "Plastic Section", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Appliances", "Counter Incharge (A+)", "Counter Incharge/AFM", "Nithiya", "A+", 15000, "Female")
    add(F, "Appliances", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Mobile", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 18000, "Male")
    add(F, "Mobile", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Fashion Jewel", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 13000, "Female")
    add(F, "Fashion Jewel", "Sales (A)", "Sales", "Vinothkumar", "A", 13000, "Male")
    add(F, "Fashion Jewel", "Sales (A)", "Sales", "Vanitha", "A", 12000, "Female")
    add(F, "Stationary", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 12000, "Female")
    add(F, "Stationary", "Sales (C)", "Sales", "", "C", 9000, "Male")
    add(F, "Foot Wear", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 16000, "Male")
    add(F, "Foot Wear", "Sales (A)", "Sales", "", "A", 13000, "Female")
    add(F, "Foot Wear", "Sales (C)", "Sales", "", "C", 9000, "Female")
    add(F, "Part Time Pool", "Part Time", "Sales", "Dharsan", "D", 8000, "Male")
    add(F, "Part Time Pool", "Part Time", "Sales", "Thamaraiselvi", "D", 8000, "Female")
    add(F, "Part Time Pool", "Part Time", "Sales", "Roja", "D", 8000, "Female")
    add(F, "Part Time Pool", "Part Time", "Sales", "Sneha", "D", 8000, "Female")
    add(F, "Part Time Pool", "Part Time", "Sales", "Sarathi", "D", 8000, "Male")
    add(F, "Part Time Pool", "Part Time", "Sales", "Nandhakumar", "D", 8000, "Male")
    add(F, "Part Time Pool", "Part Time", "Packing", "Nivaetha Lakshmi", "D", 8000, "Female")

    # ---------------- RSM (JEWELLERY) ----------------
    F = "RSM (Jewellery)"
    add(F, "Floor Management", "Designation", "Floor Manager", "Vinoth Kumar", "A+", 18000, "Male")
    add(F, "Floor Management", "Designation", "Asst. Floor Manager", "Surentharnath", "A+", 17000, "Male")
    add(F, "Cashier", "Cash Team", "Cashier (Cash-1)", "Surya", "A+", 17000, "Male")
    add(F, "Cashier", "Cash Team", "Delivery Section", "", "A+", 0, "Male")
    add(F, "Cashier", "Cash Team", "Chit Executive", "Revathi", "A+", 13000, "Female")
    add(F, "Chain Counter", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 12000, "Female")
    add(F, "Chain Counter", "Sales (C)", "Sales", "Nisha", "C", 10000, "Female")
    add(F, "Haram Counter", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 12000, "Female")
    add(F, "Haram Counter", "Sales (C)", "Sales", "Naveen", "C", 12000, "Male")
    add(F, "Stud Counter", "Counter Incharge (A+)", "Counter Incharge", "Nathiya", "A+", 13000, "Female")
    add(F, "Stud Counter", "Sales (C)", "Sales", "Gracy", "C", 9000, "Female")
    add(F, "Ring Counter", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 12000, "Female")
    add(F, "Ring Counter", "Sales (B)", "Sales", "Kiruthika", "B", 10000, "Female")
    add(F, "Diamond Counter", "Counter Incharge (A+)", "Counter Incharge", "", "A+", 16000, "Male")
    add(F, "Diamond Counter", "Sales (A)", "Sales", "", "A", 12000, "Female")
    add(F, "Silver Ornaments", "Counter Incharge (A+)", "Counter Incharge", "Sangeetha", "A+", 15000, "Female")
    add(F, "Silver Ornaments", "Sales (C)", "Sales", "Indra", "C", 10000, "Female")
    add(F, "Silver Articals", "Counter Incharge (A+)", "Counter Incharge", "Karthika", "A+", 9500, "Female")
    add(F, "Silver Articals", "Sales (C)", "Sales", "Poongothai", "C", 10000, "Female")
    add(F, "Part Time Pool", "Part Time", "Sales", "Anusha", "D", 8000, "Female")
    add(F, "Part Time Pool", "Part Time", "Sales", "Pooja sri", "D", 8000, "Male")
    add(F, "Part Time Pool", "Part Time", "Sales", "Anuja", "D", 8000, "Male")
    add(F, "Part Time Pool", "Part Time", "Sales", "Saraulatha", "D", 8000, "Female")
    add(F, "Part Time Pool", "Part Time", "Delivery", "Kaviya", "D", 8000, "Female")
    add(F, "Part Time Pool", "Part Time", "Sales", "", "D", 8000, "Female")

    # ---------------- BACKEND OFFICE (CORE TEAM) ----------------
    F = "Backend Office"
    add(F, "Core Team", "Designation Core 1", "General Manager", "Sadam Hussian", "A+", 23000, "Male")
    add(F, "Core Team", "Designation Core 1", "Admin", "Nandhakumar", "A+", 21000, "Male")
    add(F, "Core Team", "Designation Core 1", "HRM", "Arun Kumar", "A+", 20000, "Male")
    add(F, "Core Team", "Designation Core 2", "Inventry Manager", "Ravi Kumar", "A+", 21000, "Male")
    add(F, "EDP & Entry", "EDP & Entry", "Technical Support", "Ajith", "A", 14000, "Male")
    add(F, "EDP & Entry", "EDP & Entry", "Textiles EDP Head", "Janarthanan", "A+", 17000, "Male")
    add(F, "EDP & Entry", "EDP & Entry", "Textiles EDP 1", "Vijay", "A+", 14000, "Male")
    add(F, "EDP & Entry", "EDP & Entry", "Textiles EDP 2", "", "A+", 14000, "Male")
    add(F, "EDP & Entry", "EDP & Entry", "Data Entry Head", "Padma Bala", "A+", 13000, "Female")
    add(F, "EDP & Entry", "EDP & Entry", "Data Entry 1", "", "A", 12000, "Female")
    add(F, "EDP & Entry", "EDP & Entry", "Data Entry 2", "", "A", 12000, "Male")
    add(F, "Jewel EDP & Data Entry", "Jewel EDP & Data Entry", "Jewel EDP 1", "", "A+", 16000, "Male")
    add(F, "Jewel EDP & Data Entry", "Jewel EDP & Data Entry", "Data Entry 1", "", "A", 12000, "Female")
    add(F, "HR Department", "HR Dep", "HRE", "", "A+", 16000, "Female")
    add(F, "HR Department", "HR Dep", "HRA", "", "A", 14000, "Female")
    add(F, "Online Department", "Online Dep", "Online Sales", "", "A+", 12000, "Female")
    add(F, "Online Department", "Online Dep", "Online Sales", "", "A", 12000, "Female")
    add(F, "Online Department", "Online Dep", "Online Live", "", "A+", 14000, "Female")
    add(F, "Online Department", "Online Dep", "Online Live", "", "A", 14000, "Female")
    add(F, "Online Department", "Online Dep", "Online QC", "", "A+", 18000, "Male")
    add(F, "Online Department", "Online Dep", "Online QC", "", "A", 14000, "Male")
    add(F, "Online Department", "Online Dep", "Online Bill", "", "A", 14000, "Male")
    add(F, "Online Department", "Online Dep", "Online Dispatch", "", "A", 14000, "Male")
    add(F, "Editing Department", "Editing Dep", "Editor Head", "", "A+", 18000, "Male")
    add(F, "Editing Department", "Editing Dep", "Editor 1", "", "A", 14000, "Male")

    # ---------------- ENTRANCE (SUPPORT STAFF) ----------------
    F = "Entrance"
    add(F, "Entrance Management", "Designation", "Entrance Incharge", "Siva Selvi", "A+", 12000, "Female")
    add(F, "Entrance Management", "Designation", "Head Security", "Jaya Kumar", "A+", 17000, "Male")
    add(F, "Entrance", "Welcome Staff", "Welcome Staff", "Nathiya", "A+", 11000, "Female")
    add(F, "Entrance", "Welcome Staff", "Welcome Staff", "", "A", 0, "Female")
    add(F, "Entrance", "Security", "Security", "Bharathi", "B", 14000, "Male")
    add(F, "Entrance", "Building Maintenance", "Building Manager", "Nehru", "A+", 18000, "Male")
    add(F, "Entrance", "Building Maintenance", "Building Supervisor", "", "", 0, "Male")
    add(F, "Entrance", "Vehicle Handler", "Vehicle Handler", "Srinivasan", "A", 12500, "Male")
    add(F, "Entrance", "Parking Incharge", "Parking Incharge", "Rajamanickam", "C", 11000, "Male")
    add(F, "Entrance", "Vehicle Handler", "Vehicle Handler", "Perumal", "B", 12000, "Male")
    add(F, "Entrance", "Vehicle Handler", "Vehicle Handler", "", "B", 12000, "Male")
    add(F, "Entrance", "Night Security", "Night Security", "Mohammed Shafi", "B", 11000, "Male")
    add(F, "Entrance", "Night Security", "Night Security", "Subramani", "B", 0, "Male")
    add(F, "Entrance", "House Keeping", "House Keeping", "Kullamal", "A", 12000, "Female")
    add(F, "Entrance", "House Keeping", "House Keeping", "Sulomani", "B", 10000, "Female")
    add(F, "Entrance", "House Keeping", "House Keeping", "Nisha", "A", 14500, "Female")
    add(F, "Entrance", "House Keeping", "House Keeping", "Revathi", "A", 12000, "Female")

    return rows


# =================================================================
# Database layer
# =================================================================

def init_manpower_db():
    """Creates the manpower_positions table if needed, and seeds it
    with the printed report's data the first time it's empty."""
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS manpower_positions (
            pos_id INTEGER PRIMARY KEY AUTOINCREMENT,
            floor TEXT NOT NULL,
            department TEXT NOT NULL,
            category TEXT NOT NULL,
            designation TEXT NOT NULL,
            staff_name TEXT NOT NULL DEFAULT '',
            grade TEXT NOT NULL DEFAULT '',
            salary_package REAL NOT NULL DEFAULT 0,
            gender TEXT NOT NULL DEFAULT '',
            sort_order INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()

    cur.execute("SELECT COUNT(*) AS n FROM manpower_positions")
    if cur.fetchone()["n"] == 0:
        for i, row in enumerate(_seed_rows()):
            floor, dept, cat, desig, name, grade, salary, gender = row
            cur.execute("""
                INSERT INTO manpower_positions
                    (floor, department, category, designation, staff_name,
                     grade, salary_package, gender, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (floor, dept, cat, desig, name, grade, salary, gender, i))
        conn.commit()
    conn.close()


def get_floors() -> list:
    """Distinct floors present in the data, in report order."""
    conn = db.get_connection()
    rows = conn.execute("SELECT DISTINCT floor FROM manpower_positions").fetchall()
    conn.close()
    floors = [r["floor"] for r in rows]
    return sorted(floors, key=_floor_sort_key)


def get_departments(floor: str = None) -> list:
    """Distinct departments/counters, optionally scoped to one floor."""
    conn = db.get_connection()
    if floor and floor != ALL_FLOORS:
        rows = conn.execute(
            "SELECT DISTINCT department FROM manpower_positions WHERE floor = ? "
            "ORDER BY MIN(sort_order)" if False else
            "SELECT DISTINCT department FROM manpower_positions WHERE floor = ?",
            (floor,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT DISTINCT department FROM manpower_positions").fetchall()
    conn.close()
    return sorted({r["department"] for r in rows})


def list_positions(floor: str = None, department: str = None) -> list:
    """All position rows matching the filters, in seeded report order."""
    conn = db.get_connection()
    query = "SELECT * FROM manpower_positions WHERE 1=1"
    params = []
    if floor and floor != ALL_FLOORS:
        query += " AND floor = ?"
        params.append(floor)
    if department and department != ALL_DEPARTMENTS:
        query += " AND department = ?"
        params.append(department)
    query += " ORDER BY sort_order"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_position(pos_id: int) -> dict:
    conn = db.get_connection()
    row = conn.execute("SELECT * FROM manpower_positions WHERE pos_id = ?", (pos_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_position(data: dict) -> int:
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 AS n FROM manpower_positions")
    next_order = cur.fetchone()["n"]
    cur.execute("""
        INSERT INTO manpower_positions
            (floor, department, category, designation, staff_name,
             grade, salary_package, gender, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data["floor"], data["department"], data["category"], data["designation"],
          data.get("staff_name", ""), data.get("grade", ""),
          float(data.get("salary_package", 0) or 0), data.get("gender", ""), next_order))
    conn.commit()
    pos_id = cur.lastrowid
    conn.close()
    return pos_id


def update_position(pos_id: int, data: dict):
    conn = db.get_connection()
    conn.execute("""
        UPDATE manpower_positions
        SET floor = ?, department = ?, category = ?, designation = ?,
            staff_name = ?, grade = ?, salary_package = ?, gender = ?
        WHERE pos_id = ?
    """, (data["floor"], data["department"], data["category"], data["designation"],
          data.get("staff_name", ""), data.get("grade", ""),
          float(data.get("salary_package", 0) or 0), data.get("gender", ""), pos_id))
    conn.commit()
    conn.close()


def delete_position(pos_id: int):
    conn = db.get_connection()
    conn.execute("DELETE FROM manpower_positions WHERE pos_id = ?", (pos_id,))
    conn.commit()
    conn.close()


# =================================================================
# Derived summaries - always computed from the roster, never
# hand-entered separately, so they can't drift out of sync.
# =================================================================

def get_category_summary(floor: str = None) -> dict:
    """
    Category-wise breakdown for a floor (or across all floors if
    floor is None / ALL_FLOORS): allocated headcount + budget, current
    (filled) headcount + pay, vacancy count, vacancy %.

    Returns:
        {
            "floor": floor or "All Floors",
            "categories": [
                {"category", "allocated", "budget", "current",
                 "current_pay", "vacant", "vacancy_pct"}, ...
            ],  # in CATEGORY_ORDER
            "total_allocated", "total_budget", "total_current",
            "total_current_pay", "total_vacant", "total_vacancy_pct",
        }
    """
    positions = list_positions(floor=floor)
    by_cat = {}
    for p in positions:
        c = by_cat.setdefault(p["category"], {
            "category": p["category"], "allocated": 0, "budget": 0.0,
            "current": 0, "current_pay": 0.0, "vacant": 0,
        })
        c["allocated"] += 1
        c["budget"] += p["salary_package"]
        if p["staff_name"].strip():
            c["current"] += 1
            c["current_pay"] += p["salary_package"]
        else:
            c["vacant"] += 1

    categories = []
    for c in sorted(by_cat.values(), key=lambda r: _cat_sort_key(r["category"])):
        pct = (c["vacant"] / c["allocated"] * 100) if c["allocated"] else 0.0
        c["vacancy_pct"] = round(pct, 1)
        c["budget"] = round(c["budget"], 2)
        c["current_pay"] = round(c["current_pay"], 2)
        categories.append(c)

    total_allocated = sum(c["allocated"] for c in categories)
    total_vacant = sum(c["vacant"] for c in categories)
    return {
        "floor": floor if floor and floor != ALL_FLOORS else ALL_FLOORS,
        "categories": categories,
        "total_allocated": total_allocated,
        "total_budget": round(sum(c["budget"] for c in categories), 2),
        "total_current": sum(c["current"] for c in categories),
        "total_current_pay": round(sum(c["current_pay"] for c in categories), 2),
        "total_vacant": total_vacant,
        "total_vacancy_pct": round((total_vacant / total_allocated * 100) if total_allocated else 0.0, 1),
    }


def get_department_summary(floor: str = None) -> list:
    """Department/counter-wise rollup (allocated, current, vacant, budget),
    for the 'department wise' drill-down view."""
    positions = list_positions(floor=floor)
    by_dept = {}
    for p in positions:
        key = (p["floor"], p["department"])
        d = by_dept.setdefault(key, {
            "floor": p["floor"], "department": p["department"],
            "allocated": 0, "budget": 0.0, "current": 0, "vacant": 0,
        })
        d["allocated"] += 1
        d["budget"] += p["salary_package"]
        if p["staff_name"].strip():
            d["current"] += 1
        else:
            d["vacant"] += 1
    rows = list(by_dept.values())
    for d in rows:
        d["budget"] = round(d["budget"], 2)
    rows.sort(key=lambda r: (_floor_sort_key(r["floor"]), r["department"]))
    return rows


def get_overall_summary() -> dict:
    """Grand total across every floor - the 'OVER ALL MAN-POWER BUDGET' view."""
    return get_category_summary(floor=None)


def get_floor_totals() -> list:
    """One row per floor: allocated/current/vacant headcount + budget -
    for a top-level 'which floor needs attention' view."""
    rows = []
    for floor in get_floors():
        s = get_category_summary(floor=floor)
        rows.append({
            "floor": floor,
            "allocated": s["total_allocated"],
            "current": s["total_current"],
            "vacant": s["total_vacant"],
            "vacancy_pct": s["total_vacancy_pct"],
            "budget": s["total_budget"],
        })
    return rows


# =================================================================
