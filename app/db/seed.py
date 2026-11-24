import uuid
from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.models.entities import (
    Vendor,
    Product,
    VendorProduct,
    ComplianceRule,
)
from app.core.logging import logger


def seed_database(db: Session = None):
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # Check if already seeded
        if db.query(Vendor).count() > 0:
            logger.info("Database already seeded with vendors. Skipping seed.")
            return

        logger.info("Seeding database with realistic fictional procurement data...")

        # 1. Seed Compliance Rules
        compliance_rules = [
            ComplianceRule(
                rule_id=str(uuid.uuid4()),
                rule_name="Active Vendor Verification",
                description="The vendor must have active status in the corporate ERP directory.",
                rule_type="VENDOR_ACTIVE",
                threshold={"required_status": True},
                mandatory_flag=True,
                active_status=True,
            ),
            ComplianceRule(
                rule_id=str(uuid.uuid4()),
                rule_name="Minimum Warranty Enforcement",
                description="Supplied equipment must meet or exceed the mandatory warranty duration specified in the purchase request.",
                rule_type="MIN_WARRANTY",
                threshold={"min_months": 24},
                mandatory_flag=True,
                active_status=True,
            ),
            ComplianceRule(
                rule_id=str(uuid.uuid4()),
                rule_name="Delivery Deadline Adherence",
                description="Promised vendor delivery timeline must not exceed the required delivery deadline.",
                rule_type="MAX_DELIVERY",
                threshold={"max_days": 14},
                mandatory_flag=True,
                active_status=True,
            ),
            ComplianceRule(
                rule_id=str(uuid.uuid4()),
                rule_name="Inventory Stock Sufficiency",
                description="Vendor must possess sufficient on-hand inventory to fulfill the requested order quantity without supply chain delay.",
                rule_type="STOCK_AVAILABILITY",
                threshold={"fulfillment_ratio": 1.0},
                mandatory_flag=True,
                active_status=True,
            ),
            ComplianceRule(
                rule_id=str(uuid.uuid4()),
                rule_name="Quality & Vendor Rating Threshold",
                description="Vendor historical quality score must meet minimum benchmark rating of 3.8 / 5.0.",
                rule_type="VENDOR_RATING",
                threshold={"min_rating": 3.8},
                mandatory_flag=False,
                active_status=True,
            ),
        ]
        db.add_all(compliance_rules)

        # 2. Seed Vendors (8+ vendors with active/inactive, ratings, contact info)
        v_nexus = Vendor(
            vendor_id="vend-nexus-01",
            vendor_name="Nexus Tech Enterprise Solutions",
            contact_email="sales@nexustech.example.com",
            phone="+91-98200-11223",
            address="Plot 42, Tech Park Phase 2, Whitefield, Bengaluru, KA - 560066",
            active_status=True,
            vendor_rating=Decimal("4.85"),
        )
        v_apex = Vendor(
            vendor_id="vend-apex-02",
            vendor_name="Apex Global Systems Ltd",
            contact_email="orders@apexsys.example.com",
            phone="+91-98101-33445",
            address="Cyber Gateway, HITEC City, Hyderabad, TG - 500081",
            active_status=True,
            vendor_rating=Decimal("4.60"),
        )
        v_zenith = Vendor(
            vendor_id="vend-zenith-03",
            vendor_name="Zenith Infotech Solutions",
            contact_email="b2b@zenithinfo.example.com",
            phone="+91-98300-55667",
            address="Sector V, Salt Lake Electronics Complex, Kolkata, WB - 700091",
            active_status=True,
            vendor_rating=Decimal("4.25"),
        )
        v_orion = Vendor(
            vendor_id="vend-orion-04",
            vendor_name="Orion Compute Direct",
            contact_email="enterprise@oriondirect.example.com",
            phone="+91-98450-77889",
            address="Bandra Kurla Complex, Bandra East, Mumbai, MH - 400051",
            active_status=True,
            vendor_rating=Decimal("4.70"),
        )
        v_quantum = Vendor(
            vendor_id="vend-quantum-05",
            vendor_name="Quantum Byte Technologies",
            contact_email="contracts@quantumbyte.example.com",
            phone="+91-98710-99001",
            address="DLF Cyber City, Phase 3, Gurugram, HR - 122002",
            active_status=True,
            vendor_rating=Decimal("3.95"),
        )
        v_strata = Vendor(
            vendor_id="vend-strata-06",
            vendor_name="Strata Networks & Devices",
            contact_email="info@stratanet.example.com",
            phone="+91-98400-22334",
            address="Tidel Park, Rajiv Gandhi Salai, Chennai, TN - 600113",
            active_status=True,
            vendor_rating=Decimal("4.40"),
        )
        v_legacy = Vendor(
            vendor_id="vend-legacy-07",
            vendor_name="Legacy Hardware Distributors (Inactive)",
            contact_email="support@legacyhd.example.com",
            phone="+91-98220-44556",
            address="Industrial Estate, Okhla Phase 1, New Delhi, DL - 110020",
            active_status=False,  # Inactive - Compliance test case
            vendor_rating=Decimal("2.90"),
        )
        v_vanguard = Vendor(
            vendor_id="vend-vanguard-08",
            vendor_name="Vanguard Office & IT Supplies",
            contact_email="b2b@vanguardit.example.com",
            phone="+91-98800-66778",
            address="Infocity, Gandhinagar, GJ - 382009",
            active_status=True,
            vendor_rating=Decimal("4.10"),
        )

        db.add_all([v_nexus, v_apex, v_zenith, v_orion, v_quantum, v_strata, v_legacy, v_vanguard])
        db.flush()

        # 3. Seed Products (12+ products across categories)
        products = [
            # Laptops
            Product(
                product_id="prod-laptop-01",
                product_name="ThinkPad T14 Gen 4 Enterprise Laptop",
                category="Laptops",
                specifications={"cpu": "Intel Core i7-1365U", "ram_gb": 16, "storage_gb": 512, "ssd": True, "display_inch": 14.0, "os": "Windows 11 Pro"},
            ),
            Product(
                product_id="prod-laptop-02",
                product_name="Dell Latitude 5540 Business Laptop",
                category="Laptops",
                specifications={"cpu": "Intel Core i5-1345U", "ram_gb": 16, "storage_gb": 512, "ssd": True, "display_inch": 15.6, "os": "Windows 11 Pro"},
            ),
            Product(
                product_id="prod-laptop-03",
                product_name="HP EliteBook 840 G10 Professional",
                category="Laptops",
                specifications={"cpu": "Intel Core i7-1370P", "ram_gb": 32, "storage_gb": 1024, "ssd": True, "display_inch": 14.0, "os": "Windows 11 Pro"},
            ),
            Product(
                product_id="prod-laptop-04",
                product_name="Apple MacBook Pro 14 M3 Enterprise",
                category="Laptops",
                specifications={"cpu": "Apple M3 Pro 11-Core", "ram_gb": 18, "storage_gb": 512, "ssd": True, "display_inch": 14.2, "os": "macOS Sonoma"},
            ),
            # Servers
            Product(
                product_id="prod-server-01",
                product_name="PowerEdge R760 2U Rackmount Server",
                category="Servers",
                specifications={"cpu": "Dual Intel Xeon Silver 4410Y", "ram_gb": 128, "storage_tb": 8, "raid": "PERC H755", "form_factor": "2U Rack"},
            ),
            Product(
                product_id="prod-server-02",
                product_name="HPE ProLiant DL380 Gen11 Cloud Server",
                category="Servers",
                specifications={"cpu": "Dual AMD EPYC 9124", "ram_gb": 256, "storage_tb": 16, "raid": "MR416i-o", "form_factor": "2U Rack"},
            ),
            # Displays
            Product(
                product_id="prod-display-01",
                product_name="Dell UltraSharp U2724D 27-inch QHD Monitor",
                category="Displays",
                specifications={"resolution": "2560x1440 QHD", "panel": "IPS Black", "refresh_hz": 120, "connectivity": ["USB-C", "DisplayPort 1.4", "HDMI 2.1"]},
            ),
            Product(
                product_id="prod-display-02",
                product_name="LG 34WN80C-B 34-inch Curved UltraWide",
                category="Displays",
                specifications={"resolution": "3440x1440 WQHD", "panel": "IPS Curved", "refresh_hz": 60, "power_delivery_w": 60},
            ),
            # Networking
            Product(
                product_id="prod-network-01",
                product_name="Cisco Catalyst 9200L 48-Port PoE+ Gigabit Switch",
                category="Networking",
                specifications={"ports": 48, "poe_budget_w": 370, "uplinks": "4x 10G SFP+", "layer": "Layer 3 Lite"},
            ),
            Product(
                product_id="prod-network-02",
                product_name="Aruba CX 6200F 24-Port Managed Switch",
                category="Networking",
                specifications={"ports": 24, "poe_budget_w": 370, "uplinks": "4x SFP56", "layer": "Enterprise Layer 3"},
            ),
            # Ergonomic Office Furniture
            Product(
                product_id="prod-workstation-01",
                product_name="Steelcase Gesture Ergonomic Task Chair",
                category="Workstations",
                specifications={"lumbar_support": "Active 3D", "armrests": "360-degree adjustable", "warranty_years": 12, "weight_capacity_kg": 180},
            ),
            Product(
                product_id="prod-workstation-02",
                product_name="Herman Miller Aeron Chair Fully Loaded",
                category="Workstations",
                specifications={"size": "Size B (Medium)", "pellicle": "Graphite", "posture_fit": "PostureFit SL Dual Pad", "warranty_years": 12},
            ),
        ]
        db.add_all(products)
        db.flush()

        # 4. Seed Vendor Products & Quotation catalog with pricing, stock, warranty, delivery
        vendor_products = [
            # Laptop 1: ThinkPad T14 Gen 4
            # Nexus Tech: Competitive price, 36m warranty, 10 days delivery, 120 stock
            VendorProduct(
                vendor_product_id="vp-01",
                vendor_id=v_nexus.vendor_id,
                product_id="prod-laptop-01",
                unit_price=Decimal("68000.00"),
                currency="INR",
                stock_quantity=120,
                delivery_days=10,
                warranty_months=36,
                minimum_order_quantity=5,
                discount_rules={"tiers": [{"min_qty": 20, "discount_pct": 5.0}, {"min_qty": 50, "discount_pct": 8.0}]},
            ),
            # Apex Global: Slightly higher price, 24m warranty, 7 days delivery, 65 stock
            VendorProduct(
                vendor_product_id="vp-02",
                vendor_id=v_apex.vendor_id,
                product_id="prod-laptop-01",
                unit_price=Decimal("69500.00"),
                currency="INR",
                stock_quantity=65,
                delivery_days=7,
                warranty_months=24,
                minimum_order_quantity=10,
                discount_rules={"tiers": [{"min_qty": 30, "discount_pct": 4.0}, {"min_qty": 50, "discount_pct": 6.5}]},
            ),
            # Zenith Infotech: Low price but only 12 months warranty (Non-compliant for >=24m requirement!), 12 days, 90 stock
            VendorProduct(
                vendor_product_id="vp-03",
                vendor_id=v_zenith.vendor_id,
                product_id="prod-laptop-01",
                unit_price=Decimal("64000.00"),
                currency="INR",
                stock_quantity=90,
                delivery_days=12,
                warranty_months=12,  # Non-compliant with 24m warranty!
                minimum_order_quantity=1,
                discount_rules={"tiers": [{"min_qty": 25, "discount_pct": 3.0}]},
            ),
            # Orion Compute: Premium, 36m warranty, 5 days fast delivery, 80 stock
            VendorProduct(
                vendor_product_id="vp-04",
                vendor_id=v_orion.vendor_id,
                product_id="prod-laptop-01",
                unit_price=Decimal("71000.00"),
                currency="INR",
                stock_quantity=80,
                delivery_days=5,
                warranty_months=36,
                minimum_order_quantity=5,
                discount_rules={"tiers": [{"min_qty": 20, "discount_pct": 6.0}, {"min_qty": 50, "discount_pct": 10.0}]},
            ),
            # Quantum Byte: Late delivery (20 days, non-compliant with 14-day deadline!), 24m warranty, 40 stock
            VendorProduct(
                vendor_product_id="vp-05",
                vendor_id=v_quantum.vendor_id,
                product_id="prod-laptop-01",
                unit_price=Decimal("66500.00"),
                currency="INR",
                stock_quantity=40,
                delivery_days=20,  # Non-compliant with 14 days!
                warranty_months=24,
                minimum_order_quantity=5,
                discount_rules={"tiers": [{"min_qty": 20, "discount_pct": 4.0}]},
            ),
            # Strata: Low stock (15 units - insufficient for 50 unit request!)
            VendorProduct(
                vendor_product_id="vp-06",
                vendor_id=v_strata.vendor_id,
                product_id="prod-laptop-01",
                unit_price=Decimal("67500.00"),
                currency="INR",
                stock_quantity=15,  # Insufficient stock for 50 units!
                delivery_days=9,
                warranty_months=24,
                minimum_order_quantity=1,
                discount_rules={"tiers": []},
            ),
            # Legacy Hardware (Inactive vendor - non-compliant!)
            VendorProduct(
                vendor_product_id="vp-07",
                vendor_id=v_legacy.vendor_id,
                product_id="prod-laptop-01",
                unit_price=Decimal("61000.00"),
                currency="INR",
                stock_quantity=100,
                delivery_days=10,
                warranty_months=24,
                minimum_order_quantity=1,
                discount_rules={},
            ),
            # Vanguard: Moderate price, 24m warranty, 11 days delivery, 150 stock
            VendorProduct(
                vendor_product_id="vp-08",
                vendor_id=v_vanguard.vendor_id,
                product_id="prod-laptop-01",
                unit_price=Decimal("70000.00"),
                currency="INR",
                stock_quantity=150,
                delivery_days=11,
                warranty_months=24,
                minimum_order_quantity=10,
                discount_rules={"tiers": [{"min_qty": 50, "discount_pct": 7.0}]},
            ),

            # Laptop 2: Dell Latitude 5540
            VendorProduct(
                vendor_product_id="vp-09",
                vendor_id=v_nexus.vendor_id,
                product_id="prod-laptop-02",
                unit_price=Decimal("65000.00"),
                currency="INR",
                stock_quantity=110,
                delivery_days=8,
                warranty_months=36,
                minimum_order_quantity=5,
                discount_rules={"tiers": [{"min_qty": 50, "discount_pct": 7.5}]},
            ),
            VendorProduct(
                vendor_product_id="vp-10",
                vendor_id=v_apex.vendor_id,
                product_id="prod-laptop-02",
                unit_price=Decimal("66000.00"),
                currency="INR",
                stock_quantity=85,
                delivery_days=10,
                warranty_months=24,
                minimum_order_quantity=5,
                discount_rules={"tiers": [{"min_qty": 50, "discount_pct": 6.0}]},
            ),

            # Servers: PowerEdge R760
            VendorProduct(
                vendor_product_id="vp-11",
                vendor_id=v_apex.vendor_id,
                product_id="prod-server-01",
                unit_price=Decimal("485000.00"),
                currency="INR",
                stock_quantity=20,
                delivery_days=14,
                warranty_months=36,
                minimum_order_quantity=1,
                discount_rules={"tiers": [{"min_qty": 5, "discount_pct": 8.0}]},
            ),
            VendorProduct(
                vendor_product_id="vp-12",
                vendor_id=v_orion.vendor_id,
                product_id="prod-server-01",
                unit_price=Decimal("495000.00"),
                currency="INR",
                stock_quantity=15,
                delivery_days=10,
                warranty_months=36,
                minimum_order_quantity=1,
                discount_rules={"tiers": [{"min_qty": 5, "discount_pct": 10.0}]},
            ),

            # Displays: Dell UltraSharp
            VendorProduct(
                vendor_product_id="vp-13",
                vendor_id=v_nexus.vendor_id,
                product_id="prod-display-01",
                unit_price=Decimal("38000.00"),
                currency="INR",
                stock_quantity=200,
                delivery_days=5,
                warranty_months=36,
                minimum_order_quantity=5,
                discount_rules={"tiers": [{"min_qty": 20, "discount_pct": 5.0}]},
            ),
            VendorProduct(
                vendor_product_id="vp-14",
                vendor_id=v_strata.vendor_id,
                product_id="prod-display-01",
                unit_price=Decimal("39500.00"),
                currency="INR",
                stock_quantity=90,
                delivery_days=7,
                warranty_months=36,
                minimum_order_quantity=1,
                discount_rules={},
            ),

            # Networking: Cisco Catalyst 9200L
            VendorProduct(
                vendor_product_id="vp-15",
                vendor_id=v_strata.vendor_id,
                product_id="prod-network-01",
                unit_price=Decimal("175000.00"),
                currency="INR",
                stock_quantity=25,
                delivery_days=12,
                warranty_months=60,
                minimum_order_quantity=1,
                discount_rules={"tiers": [{"min_qty": 4, "discount_pct": 10.0}]},
            ),
            VendorProduct(
                vendor_product_id="vp-16",
                vendor_id=v_orion.vendor_id,
                product_id="prod-network-01",
                unit_price=Decimal("182000.00"),
                currency="INR",
                stock_quantity=30,
                delivery_days=8,
                warranty_months=60,
                minimum_order_quantity=1,
                discount_rules={"tiers": [{"min_qty": 4, "discount_pct": 12.0}]},
            ),
        ]
        db.add_all(vendor_products)
        db.commit()
        logger.info("Successfully seeded database with vendors, products, compliance rules, and catalog.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
        raise e
    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    seed_database()
