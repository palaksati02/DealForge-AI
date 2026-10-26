import uuid
import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.base import Base, utc_now
from app.db.session import engine, SessionLocal
from app.db.models.entities import (
    Role,
    User,
    Vendor,
    Product,
    VendorProduct,
    VendorCertification,
    ProcurementPolicy,
    ComplianceRule,
)
from app.core.security import hash_password
from app.core.logging import logger


def seed_database(db: Session = None):
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # Check if already seeded
        if db.query(Vendor).count() >= 10:
            logger.info("Database already seeded with 10+ vendors. Skipping seed.")
            return

        logger.info("Seeding database with realistic synthetic demonstration data...")

        # 1. Seed Roles
        roles_data = [
            ("role-mgr-01", "Procurement Manager", "Procurement manager authorized to initiate requests and approve within limits"),
            ("role-fin-02", "Finance Reviewer", "Finance director authorized to approve high-value transactions and budget overruns"),
            ("role-adm-03", "Administrator", "System administrator with full policy and audit management privileges"),
        ]
        role_objs = {}
        for r_id, r_name, r_desc in roles_data:
            existing = db.query(Role).filter_by(role_name=r_name).first()
            if not existing:
                r = Role(role_id=r_id, role_name=r_name, description=r_desc, permissions={"all": True})
                db.add(r)
                role_objs[r_name] = r
            else:
                role_objs[r_name] = existing
        db.flush()

        # 2. Seed Default Users
        users_data = [
            ("user-mgr-01", "manager@dealforge.ai", "Rajesh Sharma (Procurement Lead)", "Manager@123", "Procurement Manager", "Global Procurement"),
            ("user-fin-02", "finance@dealforge.ai", "Priya Venkatesh (Finance Director)", "Finance@123", "Finance Reviewer", "Corporate Finance"),
            ("user-adm-03", "admin@dealforge.ai", "System Administrator", "Admin@123", "Administrator", "IT Operations"),
        ]
        for u_id, email, name, pwd, r_name, dept in users_data:
            if not db.query(User).filter_by(email=email).first():
                user = User(
                    user_id=u_id,
                    email=email,
                    full_name=name,
                    hashed_password=hash_password(pwd),
                    role_id=role_objs[r_name].role_id,
                    department=dept,
                    is_active=True
                )
                db.add(user)
        db.flush()

        # 3. Seed Procurement Policies
        policies = [
            ProcurementPolicy(
                policy_id="pol-auto-01",
                policy_code="POL-AUTO-APP",
                policy_name="Automated Single-Tier Approval Threshold",
                category="APPROVAL",
                threshold_amount=Decimal("1000000.00"),
                requires_finance_review=True,
                is_active=True
            ),
            ProcurementPolicy(
                policy_id="pol-iso-02",
                policy_code="POL-ISO-MANDATORY",
                policy_name="Mandatory Enterprise Security and Quality Certification",
                category="COMPLIANCE",
                threshold_amount=Decimal("500000.00"),
                mandatory_certifications=["ISO 9001", "ISO 27001", "RoHS"],
                is_active=True
            ),
            ProcurementPolicy(
                policy_id="pol-warr-03",
                policy_code="POL-WARRANTY-MIN",
                policy_name="Enterprise Hardware Minimum Warranty SLA",
                category="WARRANTY",
                min_warranty_months=24,
                is_active=True
            ),
            ProcurementPolicy(
                policy_id="pol-deliv-04",
                policy_code="POL-DELIVERY-MAX",
                policy_name="Maximum Delivery Lead Time Cap",
                category="DELIVERY",
                max_delivery_days=14,
                is_active=True
            ),
        ]
        for p in policies:
            if not db.query(ProcurementPolicy).filter_by(policy_code=p.policy_code).first():
                db.add(p)
        db.flush()

        # 4. Seed Compliance Rules
        compliance_rules = [
            ComplianceRule(
                rule_id="cr-01",
                rule_name="Active Vendor Verification",
                description="The vendor must have active status in the corporate ERP directory.",
                rule_type="VENDOR_ACTIVE",
                threshold={"required_status": True},
                mandatory_flag=True,
                active_status=True,
            ),
            ComplianceRule(
                rule_id="cr-02",
                rule_name="Minimum Warranty Enforcement",
                description="Supplied equipment must meet or exceed the mandatory warranty duration specified in the purchase request.",
                rule_type="MIN_WARRANTY",
                threshold={"min_months": 24},
                mandatory_flag=True,
                active_status=True,
            ),
            ComplianceRule(
                rule_id="cr-03",
                rule_name="Delivery Deadline Adherence",
                description="Promised vendor delivery timeline must not exceed the required delivery deadline.",
                rule_type="MAX_DELIVERY",
                threshold={"max_days": 14},
                mandatory_flag=True,
                active_status=True,
            ),
            ComplianceRule(
                rule_id="cr-04",
                rule_name="Inventory Stock Sufficiency",
                description="Vendor must possess sufficient on-hand inventory to fulfill the requested order quantity.",
                rule_type="STOCK_AVAILABILITY",
                threshold={"fulfillment_ratio": 1.0},
                mandatory_flag=True,
                active_status=True,
            ),
            ComplianceRule(
                rule_id="cr-05",
                rule_name="Quality & Vendor Rating Threshold",
                description="Vendor historical quality score must meet minimum benchmark rating of 3.8 / 5.0.",
                rule_type="VENDOR_RATING",
                threshold={"min_rating": 3.8},
                mandatory_flag=False,
                active_status=True,
            ),
            ComplianceRule(
                rule_id="cr-06",
                rule_name="Mandatory Certifications Compliance",
                description="Vendor must possess verified ISO 9001, BIS or RoHS certifications.",
                rule_type="CERTIFICATION_CHECK",
                threshold={"required_certifications": ["ISO 9001", "RoHS"]},
                mandatory_flag=True,
                active_status=True,
            ),
        ]
        for cr in compliance_rules:
            if not db.query(ComplianceRule).filter_by(rule_id=cr.rule_id).first():
                db.add(cr)
        db.flush()

        # 5. Seed 11 Synthetic Demo Vendors
        vendors_data = [
            # 1. Compliant Winner: High stock, 36m warranty, ISO 9001 / RoHS, 4.85 rating
            Vendor(
                vendor_id="vend-nexus-01",
                vendor_name="Nexus Tech Enterprise Solutions (DEMO SYNTHETIC)",
                contact_email="sales@nexustech.example.com",
                phone="+91-98200-11223",
                address="Plot 42, Tech Park Phase 2, Whitefield, Bengaluru, KA - 560066",
                active_status=True,
                vendor_rating=Decimal("4.85"),
            ),
            # 2. High Value / Requires Dual Approval
            Vendor(
                vendor_id="vend-apex-02",
                vendor_name="Apex Global Systems Ltd (DEMO SYNTHETIC)",
                contact_email="orders@apexsys.example.com",
                phone="+91-98101-33445",
                address="Cyber Gateway, HITEC City, Hyderabad, TG - 500081",
                active_status=True,
                vendor_rating=Decimal("4.60"),
            ),
            # 3. Non-Compliant Warranty: Short 12-month warranty (fails 24m policy)
            Vendor(
                vendor_id="vend-zenith-03",
                vendor_name="Zenith Infotech Solutions (DEMO SYNTHETIC)",
                contact_email="b2b@zenithinfo.example.com",
                phone="+91-98300-55667",
                address="Sector V, Salt Lake Electronics Complex, Kolkata, WB - 700091",
                active_status=True,
                vendor_rating=Decimal("4.25"),
            ),
            # 4. Negotiation Opportunity: High list price, flexible tiered bulk discounts
            Vendor(
                vendor_id="vend-orion-04",
                vendor_name="Orion Compute Direct (DEMO SYNTHETIC)",
                contact_email="enterprise@oriondirect.example.com",
                phone="+91-98450-77889",
                address="Bandra Kurla Complex, Bandra East, Mumbai, MH - 400051",
                active_status=True,
                vendor_rating=Decimal("4.70"),
            ),
            # 5. Budget Overrun: Premium pricing exceeding ₹35L budget for 50 units
            Vendor(
                vendor_id="vend-quantum-05",
                vendor_name="Quantum Byte Technologies (DEMO SYNTHETIC)",
                contact_email="contracts@quantumbyte.example.com",
                phone="+91-98710-99001",
                address="DLF Cyber City, Phase 3, Gurugram, HR - 122002",
                active_status=True,
                vendor_rating=Decimal("3.95"),
            ),
            # 6. Insufficient Stock: Only 15 units in stock vs 50 required
            Vendor(
                vendor_id="vend-strata-06",
                vendor_name="Strata Networks & Devices (DEMO SYNTHETIC)",
                contact_email="info@stratanet.example.com",
                phone="+91-98400-22334",
                address="Tidel Park, Rajiv Gandhi Salai, Chennai, TN - 600113",
                active_status=True,
                vendor_rating=Decimal("4.40"),
            ),
            # 7. Cheap but Non-Compliant Vendor: Inactive vendor (fails active status check)
            Vendor(
                vendor_id="vend-legacy-07",
                vendor_name="Legacy Hardware Distributors (DEMO SYNTHETIC - INACTIVE)",
                contact_email="support@legacyhd.example.com",
                phone="+91-98220-44556",
                address="Industrial Estate, Okhla Phase 1, New Delhi, DL - 110020",
                active_status=False,  # Inactive flag
                vendor_rating=Decimal("2.90"),
            ),
            # 8. Delivery Violation: 20 days lead time (fails 14 days deadline)
            Vendor(
                vendor_id="vend-vanguard-08",
                vendor_name="Vanguard Office & IT Supplies (DEMO SYNTHETIC)",
                contact_email="b2b@vanguardit.example.com",
                phone="+91-98800-66778",
                address="Infocity, Gandhinagar, GJ - 382009",
                active_status=True,
                vendor_rating=Decimal("4.10"),
            ),
            # 9. Missing / Unknown Certification: Certification status UNKNOWN
            Vendor(
                vendor_id="vend-stellar-09",
                vendor_name="Stellar Cloud & Hardware (DEMO SYNTHETIC)",
                contact_email="procure@stellarcloud.example.com",
                phone="+91-98600-77112",
                address="Electronic City Phase 1, Bengaluru, KA - 560100",
                active_status=True,
                vendor_rating=Decimal("4.30"),
            ),
            # 10. Unavailable / Disqualified Vendor: 0 stock, expired certifications
            Vendor(
                vendor_id="vend-phoenix-10",
                vendor_name="Phoenix Tech Labs (DEMO SYNTHETIC - DISQUALIFIED)",
                contact_email="sales@phoenixtechlabs.example.com",
                phone="+91-98500-88334",
                address="MIDC Industrial Area, Pune, MH - 411019",
                active_status=True,
                vendor_rating=Decimal("3.20"),
            ),
            # 11. Budget-Friendly Compliant Alternative: Fully certified, attractive price
            Vendor(
                vendor_id="vend-titan-11",
                vendor_name="Titan Enterprise Gear (DEMO SYNTHETIC)",
                contact_email="orders@titangear.example.com",
                phone="+91-98900-33441",
                address="Peenya Industrial Area, Bengaluru, KA - 560058",
                active_status=True,
                vendor_rating=Decimal("4.65"),
            ),
        ]

        for v in vendors_data:
            if not db.query(Vendor).filter_by(vendor_id=v.vendor_id).first():
                db.add(v)
        db.flush()

        # 6. Seed Vendor Certifications
        now = datetime.datetime.now(datetime.timezone.utc)
        one_year_later = now + datetime.timedelta(days=365)
        one_year_ago = now - datetime.timedelta(days=365)

        certifications = [
            # Nexus: ISO 9001 and RoHS VERIFIED
            VendorCertification(certification_id="cert-nx-01", vendor_id="vend-nexus-01", certification_name="ISO 9001", issued_by="BSI Assurance UK", valid_until=one_year_later, verification_status="VERIFIED"),
            VendorCertification(certification_id="cert-nx-02", vendor_id="vend-nexus-01", certification_name="RoHS", issued_by="TUV Rheinland", valid_until=one_year_later, verification_status="VERIFIED"),
            VendorCertification(certification_id="cert-nx-03", vendor_id="vend-nexus-01", certification_name="ISO 27001", issued_by="DNV GL Business Assurance", valid_until=one_year_later, verification_status="VERIFIED"),

            # Apex: ISO 9001 VERIFIED
            VendorCertification(certification_id="cert-ap-01", vendor_id="vend-apex-02", certification_name="ISO 9001", issued_by="Bureau Veritas", valid_until=one_year_later, verification_status="VERIFIED"),
            VendorCertification(certification_id="cert-ap-02", vendor_id="vend-apex-02", certification_name="RoHS", issued_by="SGS India", valid_until=one_year_later, verification_status="VERIFIED"),

            # Zenith: BIS certified
            VendorCertification(certification_id="cert-zn-01", vendor_id="vend-zenith-03", certification_name="BIS", issued_by="Bureau of Indian Standards", valid_until=one_year_later, verification_status="VERIFIED"),

            # Orion: ISO 9001 and CE
            VendorCertification(certification_id="cert-or-01", vendor_id="vend-orion-04", certification_name="ISO 9001", issued_by="TUV SUD", valid_until=one_year_later, verification_status="VERIFIED"),
            VendorCertification(certification_id="cert-or-02", vendor_id="vend-orion-04", certification_name="RoHS", issued_by="TUV SUD", valid_until=one_year_later, verification_status="VERIFIED"),

            # Quantum: ISO 9001 VERIFIED
            VendorCertification(certification_id="cert-qb-01", vendor_id="vend-quantum-05", certification_name="ISO 9001", issued_by="Intertek", valid_until=one_year_later, verification_status="VERIFIED"),

            # Strata: RoHS verified
            VendorCertification(certification_id="cert-st-01", vendor_id="vend-strata-06", certification_name="RoHS", issued_by="DEKRA", valid_until=one_year_later, verification_status="VERIFIED"),

            # Legacy: EXPIRED certification
            VendorCertification(certification_id="cert-lg-01", vendor_id="vend-legacy-07", certification_name="ISO 9001", issued_by="Local Registrar", valid_until=one_year_ago, verification_status="EXPIRED"),

            # Vanguard: BIS verified
            VendorCertification(certification_id="cert-vg-01", vendor_id="vend-vanguard-08", certification_name="BIS", issued_by="Bureau of Indian Standards", valid_until=one_year_later, verification_status="VERIFIED"),

            # Stellar: UNKNOWN verification status (Missing/unverified certification test case)
            VendorCertification(certification_id="cert-stc-01", vendor_id="vend-stellar-09", certification_name="ISO 9001", issued_by="Self-Declared", valid_until=one_year_later, verification_status="UNKNOWN"),

            # Phoenix: EXPIRED certification
            VendorCertification(certification_id="cert-ph-01", vendor_id="vend-phoenix-10", certification_name="ISO 9001", issued_by="Defunct Agency", valid_until=one_year_ago, verification_status="EXPIRED"),

            # Titan: ISO 9001, BIS and RoHS VERIFIED
            VendorCertification(certification_id="cert-ti-01", vendor_id="vend-titan-11", certification_name="ISO 9001", issued_by="BSI Group", valid_until=one_year_later, verification_status="VERIFIED"),
            VendorCertification(certification_id="cert-ti-02", vendor_id="vend-titan-11", certification_name="RoHS", issued_by="TUV Rheinland", valid_until=one_year_later, verification_status="VERIFIED"),
            VendorCertification(certification_id="cert-ti-03", vendor_id="vend-titan-11", certification_name="BIS", issued_by="Bureau of Indian Standards", valid_until=one_year_later, verification_status="VERIFIED"),
        ]

        for c in certifications:
            if not db.query(VendorCertification).filter_by(certification_id=c.certification_id).first():
                db.add(c)
        db.flush()

        # 7. Seed Products
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
                specifications={"resolution": "2560x1440", "panel": "IPS Black", "refresh_rate_hz": 120, "ports": ["HDMI", "DP", "USB-C"]},
            ),
            Product(
                product_id="prod-display-02",
                product_name="LG 34WN80C-B 34-inch UltraWide Curved Monitor",
                category="Displays",
                specifications={"resolution": "3440x1440", "panel": "IPS", "aspect_ratio": "21:9", "usb_c_power_w": 60},
            ),
            # Networking
            Product(
                product_id="prod-network-01",
                product_name="Cisco Catalyst 9300 48-Port PoE+ Switch",
                category="Networking",
                specifications={"ports": 48, "poe_budget_w": 740, "uplinks": "4x 10G SFP+", "layer": 3},
            ),
            # Workstations
            Product(
                product_id="prod-chair-01",
                product_name="Herman Miller Aeron Ergonomic Office Chair",
                category="Workstations",
                specifications={"size": "Size B", "lumbar_support": "PostureFit SL", "tilt_limiter": True, "armrests": "Fully Adjustable"},
            ),
        ]

        for p in products:
            if not db.query(Product).filter_by(product_id=p.product_id).first():
                db.add(p)
        db.flush()

        # 8. Seed Vendor Product Listings
        vendor_products = [
            # --- prod-laptop-01 (ThinkPad T14) across vendors ---
            # Nexus (Rank 1 Compliant Winner): unit_price ₹68,000, 120 stock, 10 days delivery, 36m warranty
            VendorProduct(
                vendor_product_id="vp-nx-01",
                vendor_id="vend-nexus-01",
                product_id="prod-laptop-01",
                unit_price=Decimal("68000.00"),
                stock_quantity=120,
                delivery_days=10,
                warranty_months=36,
                discount_rules={"tiers": [{"min_qty": 20, "discount_pct": 5.0}, {"min_qty": 50, "discount_pct": 8.0}]},
            ),
            # Apex (High-value / requires approval): unit_price ₹72,000, 80 stock, 8 days delivery, 36m warranty
            VendorProduct(
                vendor_product_id="vp-ap-01",
                vendor_id="vend-apex-02",
                product_id="prod-laptop-01",
                unit_price=Decimal("72000.00"),
                stock_quantity=80,
                delivery_days=8,
                warranty_months=36,
                discount_rules={"tiers": [{"min_qty": 30, "discount_pct": 4.0}, {"min_qty": 50, "discount_pct": 6.0}]},
            ),
            # Zenith (Fails Warranty: 12 months vs 24 required): unit_price ₹66,000
            VendorProduct(
                vendor_product_id="vp-zn-01",
                vendor_id="vend-zenith-03",
                product_id="prod-laptop-01",
                unit_price=Decimal("66000.00"),
                stock_quantity=60,
                delivery_days=12,
                warranty_months=12,  # Non-compliant warranty
                discount_rules={"tiers": [{"min_qty": 25, "discount_pct": 3.0}]},
            ),
            # Orion (Negotiation Opportunity): unit_price ₹70,000, big discount tiers
            VendorProduct(
                vendor_product_id="vp-or-01",
                vendor_id="vend-orion-04",
                product_id="prod-laptop-01",
                unit_price=Decimal("70000.00"),
                stock_quantity=95,
                delivery_days=9,
                warranty_months=36,
                discount_rules={"tiers": [{"min_qty": 20, "discount_pct": 6.0}, {"min_qty": 50, "discount_pct": 10.0}]},
            ),
            # Quantum (Budget Overrun Scenario): unit_price ₹78,000
            VendorProduct(
                vendor_product_id="vp-qb-01",
                vendor_id="vend-quantum-05",
                product_id="prod-laptop-01",
                unit_price=Decimal("78000.00"),
                stock_quantity=40,
                delivery_days=11,
                warranty_months=24,
                discount_rules={"tiers": [{"min_qty": 50, "discount_pct": 2.0}]},
            ),
            # Strata (Insufficient Stock: 15 units vs 50 required)
            VendorProduct(
                vendor_product_id="vp-st-01",
                vendor_id="vend-strata-06",
                product_id="prod-laptop-01",
                unit_price=Decimal("67500.00"),
                stock_quantity=15,  # Insufficient stock
                delivery_days=7,
                warranty_months=24,
                discount_rules={"tiers": []},
            ),
            # Legacy (Inactive Vendor): unit_price ₹55,000 (very cheap, but fails active compliance)
            VendorProduct(
                vendor_product_id="vp-lg-01",
                vendor_id="vend-legacy-07",
                product_id="prod-laptop-01",
                unit_price=Decimal("55000.00"),
                stock_quantity=200,
                delivery_days=5,
                warranty_months=24,
                discount_rules={"tiers": []},
            ),
            # Vanguard (Delivery Violation: 20 days vs 14 days required)
            VendorProduct(
                vendor_product_id="vp-vg-01",
                vendor_id="vend-vanguard-08",
                product_id="prod-laptop-01",
                unit_price=Decimal("65000.00"),
                stock_quantity=75,
                delivery_days=20,  # Delivery violation
                warranty_months=24,
                discount_rules={"tiers": [{"min_qty": 50, "discount_pct": 5.0}]},
            ),
            # Stellar (Missing/Unknown certification verification)
            VendorProduct(
                vendor_product_id="vp-stc-01",
                vendor_id="vend-stellar-09",
                product_id="prod-laptop-01",
                unit_price=Decimal("67000.00"),
                stock_quantity=55,
                delivery_days=11,
                warranty_months=24,
                discount_rules={"tiers": []},
            ),
            # Phoenix (Disqualified: 0 stock, out of stock)
            VendorProduct(
                vendor_product_id="vp-ph-01",
                vendor_id="vend-phoenix-10",
                product_id="prod-laptop-01",
                unit_price=Decimal("63000.00"),
                stock_quantity=0,  # Zero stock
                delivery_days=14,
                warranty_months=24,
                discount_rules={"tiers": []},
            ),
            # Titan (Budget-Friendly Compliant Alternative): unit_price ₹62,000, 100 stock, 9 days delivery, 24m warranty
            VendorProduct(
                vendor_product_id="vp-ti-01",
                vendor_id="vend-titan-11",
                product_id="prod-laptop-01",
                unit_price=Decimal("62000.00"),
                stock_quantity=100,
                delivery_days=9,
                warranty_months=24,
                discount_rules={"tiers": [{"min_qty": 20, "discount_pct": 3.0}, {"min_qty": 50, "discount_pct": 5.0}]},
            ),
            # Servers & Displays listings
            VendorProduct(
                vendor_product_id="vp-nx-srv",
                vendor_id="vend-nexus-01",
                product_id="prod-server-01",
                unit_price=Decimal("450000.00"),
                stock_quantity=12,
                delivery_days=12,
                warranty_months=36,
                discount_rules={"tiers": [{"min_qty": 2, "discount_pct": 4.0}, {"min_qty": 4, "discount_pct": 7.0}]},
            ),
            VendorProduct(
                vendor_product_id="vp-ap-srv",
                vendor_id="vend-apex-02",
                product_id="prod-server-01",
                unit_price=Decimal("465000.00"),
                stock_quantity=8,
                delivery_days=10,
                warranty_months=36,
                discount_rules={"tiers": [{"min_qty": 4, "discount_pct": 5.0}]},
            ),
            VendorProduct(
                vendor_product_id="vp-or-disp",
                vendor_id="vend-orion-04",
                product_id="prod-display-01",
                unit_price=Decimal("42000.00"),
                stock_quantity=50,
                delivery_days=7,
                warranty_months=36,
                discount_rules={"tiers": [{"min_qty": 10, "discount_pct": 5.0}]},
            ),
        ]

        for vp in vendor_products:
            if not db.query(VendorProduct).filter_by(vendor_product_id=vp.vendor_product_id).first():
                db.add(vp)
        db.flush()

        db.commit()
        logger.info("Successfully seeded 11 vendors, certifications, policies, products, and listings!")

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
        raise
    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed_database()
