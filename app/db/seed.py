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
    PurchaseRequest,
    VendorQuote,
    Evaluation,
    Negotiation,
    Approval,
    PurchaseOrder,
    WorkflowState,
    AgentLog,
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
            if db.query(PurchaseRequest).count() == 0:
                logger.info("Vendors already seeded, but no requests exist. Seeding initial procurement workflows...")
                _seed_initial_workflows(db)
            else:
                logger.info("Database already seeded with vendors and workflows. Skipping seed.")
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
        _seed_initial_workflows(db)
        logger.info("Successfully seeded database with vendors, products, compliance rules, catalog, and benchmark workflows.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
        raise e
    finally:
        if close_db:
            db.close()


def _seed_initial_workflows(db: Session):
    """Seed realistic procurement workflows, evaluated quotes, negotiations, approvals, and POs."""
    try:
        # 1. Standard Bulk Laptop Procurement (Issued PO)
        req1 = PurchaseRequest(
            request_id="req-seed-01",
            requester="IT Operations Director",
            raw_request_text="Purchase 50 laptops with at least 16 GB RAM and 512 GB SSD, a maximum budget of ₹38,00,000, delivery within 14 days, and a minimum two-year warranty.",
            product_requirements={"category": "Laptops", "specifications": {"ram_gb": 16, "storage_gb": 512, "ssd": True}},
            quantity=50,
            budget_limit=Decimal("3800000.00"),
            currency="INR",
            delivery_deadline_days=14,
            warranty_requirement_months=24,
            status="PO_CREATED"
        )
        q1 = VendorQuote(
            quote_id="quote-seed-01",
            request_id="req-seed-01",
            vendor_id="vend-nexus-01",
            unit_price=Decimal("65000.00"),
            quantity=50,
            discount=Decimal("243750.00"),
            tax=Decimal("541125.00"),
            shipping_cost=Decimal("10000.00"),
            total_amount=Decimal("3557375.00"),
            delivery_days=8,
            warranty_months=36,
            availability_status="IN_STOCK",
            quote_status="SELECTED",
            calculation_breakdown={"base_subtotal": "3250000.00", "discount_percentage": "7.5", "discount_amount": "243750.00", "taxable_amount": "3006250.00", "tax_rate_percentage": "18.0000", "tax_amount": "541125.00", "shipping_cost": "10000.00", "final_total": "3557375.00"}
        )
        ev1 = Evaluation(
            evaluation_id="eval-seed-01",
            request_id="req-seed-01",
            quote_id="quote-seed-01",
            price_score=Decimal("95.50"),
            delivery_score=Decimal("94.00"),
            warranty_score=Decimal("98.00"),
            compliance_score=Decimal("97.00"),
            specification_score=Decimal("96.00"),
            final_score=Decimal("95.85"),
            eligibility_status="ELIGIBLE",
            explanation="Optimal pricing with 7.5% volume discount, full ISO 27001 compliance, and 3-year enterprise warranty.",
            rank=1
        )
        neg1 = Negotiation(
            negotiation_id="neg-seed-01",
            request_id="req-seed-01",
            quote_id="quote-seed-01",
            original_amount=Decimal("3801125.00"),
            target_amount=Decimal("3500000.00"),
            counter_offer_amount=Decimal("3557375.00"),
            justification="Volume discount requested on bulk purchase of 50 units.",
            draft_message="We propose ₹35,57,375.00 all-inclusive based on 50-unit volume tier.",
            negotiation_status="ACCEPTED",
            vendor_response="Nexus Tech confirms acceptance of revised volume counter-offer ₹35,57,375.00 with priority 8-day dispatch."
        )
        app1 = Approval(
            approval_id="appr-seed-01",
            request_id="req-seed-01",
            quote_id="quote-seed-01",
            risk_assessment={"risk_category": "LOW", "risk_score": 12.0, "human_review_required": False, "assessed_by": "Google ADK Risk Agent via A2A"},
            approval_reason="Total value ₹35,57,375.00 exceeds ₹10,00,000 threshold.",
            requested_by="CrewAI:ApprovalCoordinator",
            decision="APPROVED",
            decided_by="VP of Enterprise Procurement",
            comments="Approved based on low ADK risk score (12.0/100) and verified ISO compliance."
        )
        po1 = PurchaseOrder(
            purchase_order_id="po-seed-01",
            request_id="req-seed-01",
            vendor_id="vend-nexus-01",
            quote_id="quote-seed-01",
            order_number="PO-DF-2026-0001",
            approved_total=Decimal("3557375.00"),
            currency="INR",
            status="ISSUED",
            approved_by="VP of Enterprise Procurement",
            order_details={"quantity": 50, "unit_price": 65000.0, "discount": 243750.0, "tax": 541125.0, "shipping_cost": 10000.0, "total_amount": 3557375.0, "currency": "INR", "delivery_days": 8, "warranty_months": 36, "calculation_breakdown": {"base_subtotal": "3250000.00", "discount_percentage": "7.5", "discount_amount": "243750.00", "taxable_amount": "3006250.00", "tax_rate_percentage": "18.0000", "tax_amount": "541125.00", "shipping_cost": "10000.00", "final_total": "3557375.00"}}
        )
        wf1 = WorkflowState(
            workflow_id="wf-seed-01",
            request_id="req-seed-01",
            current_step="PO_CREATED",
            status="COMPLETED",
            state_data={"order_number": "PO-DF-2026-0001", "approved_total": "3557375.00"}
        )

        # 2. Enterprise Server Cluster (Issued PO)
        req2 = PurchaseRequest(
            request_id="req-seed-02",
            requester="Cloud Infrastructure Lead",
            raw_request_text="Purchase 10 enterprise servers with dual Xeon processors, a maximum budget of ₹50,00,000.",
            product_requirements={"category": "Servers"},
            quantity=10,
            budget_limit=Decimal("5000000.00"),
            currency="INR",
            delivery_deadline_days=20,
            warranty_requirement_months=36,
            status="PO_CREATED"
        )
        q2 = VendorQuote(
            quote_id="quote-seed-02",
            request_id="req-seed-02",
            vendor_id="vend-orion-04",
            unit_price=Decimal("495000.00"),
            quantity=10,
            discount=Decimal("495000.00"),
            tax=Decimal("801900.00"),
            shipping_cost=Decimal("15000.00"),
            total_amount=Decimal("5271900.00"),
            delivery_days=10,
            warranty_months=36,
            availability_status="IN_STOCK",
            quote_status="SELECTED",
            calculation_breakdown={"base_subtotal": "4950000.00", "discount_percentage": "10.0", "discount_amount": "495000.00", "taxable_amount": "4455000.00", "tax_rate_percentage": "18.0000", "tax_amount": "801900.00", "shipping_cost": "15000.00", "final_total": "5271900.00"}
        )
        ev2 = Evaluation(
            evaluation_id="eval-seed-02",
            request_id="req-seed-02",
            quote_id="quote-seed-02",
            price_score=Decimal("92.00"),
            delivery_score=Decimal("96.00"),
            warranty_score=Decimal("95.00"),
            compliance_score=Decimal("97.00"),
            specification_score=Decimal("98.00"),
            final_score=Decimal("95.10"),
            eligibility_status="ELIGIBLE",
            explanation="Dell PowerEdge R760 cluster with 10% enterprise discount.",
            rank=1
        )
        app2 = Approval(
            approval_id="appr-seed-02",
            request_id="req-seed-02",
            quote_id="quote-seed-02",
            risk_assessment={"risk_category": "LOW", "risk_score": 15.0, "human_review_required": False, "assessed_by": "Google ADK Risk Agent via A2A"},
            approval_reason="High-Value Procurement (₹52,71,900.00 >= ₹10,00,000 threshold).",
            requested_by="CrewAI:ApprovalCoordinator",
            decision="APPROVED",
            decided_by="CTO & VP Infrastructure",
            comments="Approved for data center expansion."
        )
        po2 = PurchaseOrder(
            purchase_order_id="po-seed-02",
            request_id="req-seed-02",
            vendor_id="vend-orion-04",
            quote_id="quote-seed-02",
            order_number="PO-DF-2026-0002",
            approved_total=Decimal("5271900.00"),
            currency="INR",
            status="ISSUED",
            approved_by="CTO & VP Infrastructure",
            order_details={"quantity": 10, "unit_price": 495000.0, "discount": 495000.0, "tax": 801900.0, "shipping_cost": 15000.0, "total_amount": 5271900.0, "currency": "INR", "delivery_days": 10, "warranty_months": 36}
        )
        wf2 = WorkflowState(
            workflow_id="wf-seed-02",
            request_id="req-seed-02",
            current_step="PO_CREATED",
            status="COMPLETED",
            state_data={"order_number": "PO-DF-2026-0002", "approved_total": "5271900.00"}
        )

        # 3. Department 4K Displays (Auto-Approved < ₹10L Threshold)
        req3 = PurchaseRequest(
            request_id="req-seed-03",
            requester="Operations Manager",
            raw_request_text="Purchase 15 UltraSharp 4K Displays with a budget of ₹7,50,000.",
            product_requirements={"category": "Displays"},
            quantity=15,
            budget_limit=Decimal("750000.00"),
            currency="INR",
            delivery_deadline_days=10,
            warranty_requirement_months=36,
            status="PO_CREATED"
        )
        q3 = VendorQuote(
            quote_id="quote-seed-03",
            request_id="req-seed-03",
            vendor_id="vend-nexus-01",
            unit_price=Decimal("38000.00"),
            quantity=15,
            discount=Decimal("0.00"),
            tax=Decimal("102600.00"),
            shipping_cost=Decimal("5000.00"),
            total_amount=Decimal("677600.00"),
            delivery_days=5,
            warranty_months=36,
            availability_status="IN_STOCK",
            quote_status="SELECTED",
            calculation_breakdown={"base_subtotal": "570000.00", "discount_percentage": "0.0", "discount_amount": "0.00", "taxable_amount": "570000.00", "tax_rate_percentage": "18.0000", "tax_amount": "102600.00", "shipping_cost": "5000.00", "final_total": "677600.00"}
        )
        ev3 = Evaluation(
            evaluation_id="eval-seed-03",
            request_id="req-seed-03",
            quote_id="quote-seed-03",
            price_score=Decimal("94.00"),
            delivery_score=Decimal("97.00"),
            warranty_score=Decimal("98.00"),
            compliance_score=Decimal("98.00"),
            specification_score=Decimal("95.00"),
            final_score=Decimal("96.20"),
            eligibility_status="ELIGIBLE",
            explanation="5-day rapid dispatch with standard 3-year manufacturer warranty.",
            rank=1
        )
        app3 = Approval(
            approval_id="appr-seed-03",
            request_id="req-seed-03",
            quote_id="quote-seed-03",
            risk_assessment={"risk_category": "LOW", "risk_score": 8.0, "human_review_required": False, "assessed_by": "Google ADK Risk Agent via A2A"},
            approval_reason="Total value ₹6,77,600.00 is below ₹10,00,000 threshold. Auto-Approved.",
            requested_by="CrewAI:ApprovalCoordinator",
            decision="APPROVED",
            decided_by="System Auto-Approval Engine",
            comments="Straight-through STP auto-approval granted (< ₹10,00,000 ceiling)."
        )
        po3 = PurchaseOrder(
            purchase_order_id="po-seed-03",
            request_id="req-seed-03",
            vendor_id="vend-nexus-01",
            quote_id="quote-seed-03",
            order_number="PO-DF-2026-0003",
            approved_total=Decimal("677600.00"),
            currency="INR",
            status="ISSUED",
            approved_by="System Auto-Approval Engine",
            order_details={"quantity": 15, "unit_price": 38000.0, "discount": 0.0, "tax": 102600.0, "shipping_cost": 5000.0, "total_amount": 677600.0, "currency": "INR", "delivery_days": 5, "warranty_months": 36}
        )
        wf3 = WorkflowState(
            workflow_id="wf-seed-03",
            request_id="req-seed-03",
            current_step="PO_CREATED",
            status="COMPLETED",
            state_data={"order_number": "PO-DF-2026-0003", "approved_total": "677600.00"}
        )

        # 4. Pending Approval Item (Awaiting Human Sign-off in Approval Centre)
        req4 = PurchaseRequest(
            request_id="req-seed-04",
            requester="Engineering Team Lead",
            raw_request_text="Purchase 30 developer laptops with 32 GB RAM, maximum budget of ₹25,00,000.",
            product_requirements={"category": "Laptops", "specifications": {"ram_gb": 32, "storage_gb": 512, "ssd": True}},
            quantity=30,
            budget_limit=Decimal("2500000.00"),
            currency="INR",
            delivery_deadline_days=14,
            warranty_requirement_months=24,
            status="PENDING_APPROVAL"
        )
        q4 = VendorQuote(
            quote_id="quote-seed-04",
            request_id="req-seed-04",
            vendor_id="vend-nexus-01",
            unit_price=Decimal("65000.00"),
            quantity=30,
            discount=Decimal("0.00"),
            tax=Decimal("351000.00"),
            shipping_cost=Decimal("8000.00"),
            total_amount=Decimal("2309000.00"),
            delivery_days=8,
            warranty_months=36,
            availability_status="IN_STOCK",
            quote_status="EVALUATED",
            calculation_breakdown={"base_subtotal": "1950000.00", "discount_percentage": "0.0", "discount_amount": "0.00", "taxable_amount": "1950000.00", "tax_rate_percentage": "18.0000", "tax_amount": "351000.00", "shipping_cost": "8000.00", "final_total": "2309000.00"}
        )
        ev4 = Evaluation(
            evaluation_id="eval-seed-04",
            request_id="req-seed-04",
            quote_id="quote-seed-04",
            price_score=Decimal("94.50"),
            delivery_score=Decimal("95.00"),
            warranty_score=Decimal("98.00"),
            compliance_score=Decimal("97.00"),
            specification_score=Decimal("95.00"),
            final_score=Decimal("95.50"),
            eligibility_status="ELIGIBLE",
            explanation="High-performance developer configuration, within budget surplus ₹1,91,000.00.",
            rank=1
        )
        app4 = Approval(
            approval_id="appr-seed-04",
            request_id="req-seed-04",
            quote_id="quote-seed-04",
            risk_assessment={"risk_category": "LOW", "risk_score": 11.5, "human_review_required": False, "explanation": "Google ADK evaluated deal risk as 11.5/100 (LOW). Vendor demonstrates strong financial alignment, compliant terms, and acceptable SLA.", "assessed_by": "Google ADK Risk Agent via A2A"},
            approval_reason="Total value ₹23,09,000.00 exceeds ₹10,00,000 threshold. Mandatory Human Sign-Off Required.",
            requested_by="CrewAI:ApprovalCoordinator",
            decision="PENDING",
            comments=None
        )
        wf4 = WorkflowState(
            workflow_id="wf-seed-04",
            request_id="req-seed-04",
            current_step="WAITING_FOR_APPROVAL",
            status="PAUSED",
            state_data={"approval_id": "appr-seed-04", "approval_reason": "Total value ₹23,09,000.00 exceeds ₹10,00,000 threshold."}
        )

        db.add_all([
            req1, q1, ev1, neg1, app1, po1, wf1,
            req2, q2, ev2, app2, po2, wf2,
            req3, q3, ev3, app3, po3, wf3,
            req4, q4, ev4, app4, wf4,
        ])
        db.commit()
        logger.info("Successfully seeded benchmark procurement requests, quotes, evaluations, negotiations, approvals, and POs.")
    except Exception as e:
        db.rollback()
        logger.warning(f"Could not seed initial workflows: {e}")


if __name__ == "__main__":
    seed_database()
