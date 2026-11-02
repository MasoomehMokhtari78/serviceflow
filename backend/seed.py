"""
Synthetic Demo Data Seeder for ServiceFlow.
All data seeded here is strictly SYNTHETIC and designed to simulate a realistic
high-volume Iranian multi-branch café operation across four branches in Tehran.
"""

import sys
from os.path import dirname, abspath
backend_dir = dirname(abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import uuid
from datetime import datetime, timezone, timedelta
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.entities import (
    Restaurant,
    Branch,
    BranchDailyCounter,
    User,
    KitchenStation,
    Table,
    MenuCategory,
    MenuItem,
    Order,
    OrderItem,
    OrderStatusHistory,
    RoleEnum,
    StationTypeEnum,
    TableSectionEnum,
    OrderStatusEnum,
    OrderItemStatusEnum,
    utcnow,
    utcnow_date
)


def seed_data():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("[*] Seeding ServiceFlow Synthetic Demo Data...")
        print("[!] Notice: All staff, branches, and orders are 100% synthetic.")
        print("=" * 60)

        # Clear existing data to allow clean re-seeding
        db.query(OrderStatusHistory).delete()
        db.query(OrderItem).delete()
        db.query(Order).delete()
        db.query(BranchDailyCounter).delete()
        db.query(Table).delete()
        db.query(MenuItem).delete()
        db.query(MenuCategory).delete()
        db.query(KitchenStation).delete()
        db.query(User).delete()
        db.query(Branch).delete()
        db.query(Restaurant).delete()
        db.commit()


        # ----------------------------------------------------
        # 1. Primary Tenant: Character Café Group (کاراکتر کافه)
        # ----------------------------------------------------
        kariz = Restaurant(
            name="کافه کاراکتر",
            slug="kariz-cafe",
            created_at=utcnow()
        )
        db.add(kariz)
        db.flush()

        # ----------------------------------------------------
        # 2. Competitor Tenant: Sepanj Café (کافه سپنج) - for Multi-Tenancy Tests
        # ----------------------------------------------------
        sepanj = Restaurant(
            name="کافه سپنج (رقیب)",
            slug="sepanj-cafe",
            created_at=utcnow()
        )
        db.add(sepanj)
        db.flush()

        # ----------------------------------------------------
        # 3. Branches of Character Café (4 Branches in Tehran)
        # ----------------------------------------------------
        branch_enghelab = Branch(
            restaurant_id=kariz.id,
            name="شعبه انقلاب (دانشگاهی)",
            address="تهران، خیابان انقلاب، نبش وصال شیرازی",
            phone="021-66401234",
            is_active=True
        )
        branch_sanaee = Branch(
            restaurant_id=kariz.id,
            name="شعبه سنایی (بار تخصصی دمی)",
            address="تهران، خیابان سنایی، کوچه هجدهم",
            phone="021-88305678",
            is_active=True
        )
        branch_shahrak = Branch(
            restaurant_id=kariz.id,
            name="شعبه شهرک غرب (سالن و تراس بزرگ)",
            address="تهران، شهرک غرب، بلوار فرحزادی",
            phone="021-88089012",
            is_active=True
        )
        branch_fereshteh = Branch(
            restaurant_id=kariz.id,
            name="شعبه فرشته (بوتیک و موکتل)",
            address="تهران، خیابان فرشته، خیابان بوسنی هرزگوین",
            phone="021-22003456",
            is_active=True
        )
        db.add_all([branch_enghelab, branch_sanaee, branch_shahrak, branch_fereshteh])

        # Sepanj branch
        branch_sepanj = Branch(
            restaurant_id=sepanj.id,
            name="شعبه مرکزی سپنج",
            address="تهران، سعادت‌آباد",
            phone="021-22334455",
            is_active=True
        )
        db.add(branch_sepanj)
        db.flush()

        # ----------------------------------------------------
        # 4. Kitchen Stations for Branches
        # ----------------------------------------------------
        def create_branch_stations(r_id, b_id):
            return [
                KitchenStation(
                    restaurant_id=r_id,
                    branch_id=b_id,
                    name="بار اسپرسو",
                    station_type=StationTypeEnum.BARISTA,
                    target_prep_time_minutes=4,
                    display_order=1
                ),
                KitchenStation(
                    restaurant_id=r_id,
                    branch_id=b_id,
                    name="بار دمی و چای",
                    station_type=StationTypeEnum.BREW_BAR,
                    target_prep_time_minutes=8,
                    display_order=2
                ),
                KitchenStation(
                    restaurant_id=r_id,
                    branch_id=b_id,
                    name="بار سرد و موکتل",
                    station_type=StationTypeEnum.COLD_BAR,
                    target_prep_time_minutes=6,
                    display_order=3
                ),
                KitchenStation(
                    restaurant_id=r_id,
                    branch_id=b_id,
                    name="آشپزخانه و بشقاب گرم",
                    station_type=StationTypeEnum.KITCHEN,
                    target_prep_time_minutes=15,
                    display_order=4
                )
            ]

        enghelab_stations = create_branch_stations(kariz.id, branch_enghelab.id)
        sanaee_stations = create_branch_stations(kariz.id, branch_sanaee.id)
        shahrak_stations = create_branch_stations(kariz.id, branch_shahrak.id)
        fereshteh_stations = create_branch_stations(kariz.id, branch_fereshteh.id)
        sepanj_stations = create_branch_stations(sepanj.id, branch_sepanj.id)

        all_stations = enghelab_stations + sanaee_stations + shahrak_stations + fereshteh_stations + sepanj_stations
        db.add_all(all_stations)
        db.flush()

        enghelab_barista = enghelab_stations[0]
        enghelab_brew = enghelab_stations[1]
        enghelab_cold = enghelab_stations[2]
        enghelab_kitchen = enghelab_stations[3]

        # ----------------------------------------------------
        # 5. Tables for Branches
        # ----------------------------------------------------
        def create_branch_tables(r_id, b_id):
            tables = []
            # Main hall 1-8
            for i in range(1, 9):
                tables.append(Table(
                    restaurant_id=r_id,
                    branch_id=b_id,
                    table_number=f"میز {i}",
                    section=TableSectionEnum.MAIN_HALL,
                    capacity=4
                ))
            # Terrace 9-12
            for i in range(9, 13):
                tables.append(Table(
                    restaurant_id=r_id,
                    branch_id=b_id,
                    table_number=f"تراس {i}",
                    section=TableSectionEnum.TERRACE,
                    capacity=4
                ))
            # VIP 14
            tables.append(Table(
                restaurant_id=r_id,
                branch_id=b_id,
                table_number="اتاق VIP",
                section=TableSectionEnum.VIP,
                capacity=8
            ))
            return tables

        enghelab_tables = create_branch_tables(kariz.id, branch_enghelab.id)
        sanaee_tables = create_branch_tables(kariz.id, branch_sanaee.id)
        shahrak_tables = create_branch_tables(kariz.id, branch_shahrak.id)
        fereshteh_tables = create_branch_tables(kariz.id, branch_fereshteh.id)
        sepanj_tables = create_branch_tables(sepanj.id, branch_sepanj.id)

        all_tables = enghelab_tables + sanaee_tables + shahrak_tables + fereshteh_tables + sepanj_tables
        db.add_all(all_tables)
        db.flush()

        # ----------------------------------------------------
        # 6. Users & Staff Credentials
        # ----------------------------------------------------
        pw_hash = get_password_hash("password123")

        # Global Manager (all branches)
        manager = User(
            restaurant_id=kariz.id,
            branch_id=None,
            email="manager@kariz.ir",
            hashed_password=pw_hash,
            full_name="علی رضایی (مدیر ارشد)",
            role=RoleEnum.MANAGER
        )

        # Enghelab Staff
        waiter_enghelab = User(
            restaurant_id=kariz.id,
            branch_id=branch_enghelab.id,
            email="waiter.enghelab@kariz.ir",
            hashed_password=pw_hash,
            full_name="سارا حسینی (سالن‌کار انقلاب)",
            role=RoleEnum.WAITER
        )
        barista_enghelab = User(
            restaurant_id=kariz.id,
            branch_id=branch_enghelab.id,
            station_id=enghelab_barista.id,
            email="barista.enghelab@kariz.ir",
            hashed_password=pw_hash,
            full_name="نیما صادقی (باریستا انقلاب)",
            role=RoleEnum.KITCHEN
        )
        chef_enghelab = User(
            restaurant_id=kariz.id,
            branch_id=branch_enghelab.id,
            station_id=enghelab_kitchen.id,
            email="chef.enghelab@kariz.ir",
            hashed_password=pw_hash,
            full_name="امیر کریمی (شف آشپزخانه)",
            role=RoleEnum.KITCHEN
        )

        # Other Branch Waiters
        waiter_sanaee = User(
            restaurant_id=kariz.id,
            branch_id=branch_sanaee.id,
            email="waiter.sanaee@kariz.ir",
            hashed_password=pw_hash,
            full_name="روشنک راد (سالن‌کار سنایی)",
            role=RoleEnum.WAITER
        )
        waiter_shahrak = User(
            restaurant_id=kariz.id,
            branch_id=branch_shahrak.id,
            email="waiter.shahrak@kariz.ir",
            hashed_password=pw_hash,
            full_name="کیانوش پارسا (سالن‌کار شهرک)",
            role=RoleEnum.WAITER
        )
        waiter_fereshteh = User(
            restaurant_id=kariz.id,
            branch_id=branch_fereshteh.id,
            email="waiter.fereshteh@kariz.ir",
            hashed_password=pw_hash,
            full_name="درسا بهرامی (سالن‌کار فرشته)",
            role=RoleEnum.WAITER
        )

        # Sepanj Users (Tenant B)
        sepanj_manager = User(
            restaurant_id=sepanj.id,
            branch_id=None,
            email="manager@sepanj.ir",
            hashed_password=pw_hash,
            full_name="بهرام توکلی (مدیر سپنج)",
            role=RoleEnum.MANAGER
        )
        sepanj_waiter = User(
            restaurant_id=sepanj.id,
            branch_id=branch_sepanj.id,
            email="waiter@sepanj.ir",
            hashed_password=pw_hash,
            full_name="پرهام کاظمی (سالن‌کار سپنج)",
            role=RoleEnum.WAITER
        )

        # Test Users for Security & Multi-Tenant Edge Cases
        # Same email in two different tenants with different passwords
        duplicate_kariz = User(
            restaurant_id=kariz.id,
            branch_id=None,
            email="duplicate@cafegroup.ir",
            hashed_password=get_password_hash("kariz_pass_123"),
            full_name="کاربر هم‌نام (کاراکتر)",
            role=RoleEnum.MANAGER
        )
        duplicate_sepanj = User(
            restaurant_id=sepanj.id,
            branch_id=None,
            email="duplicate@cafegroup.ir",
            hashed_password=get_password_hash("sepanj_pass_456"),
            full_name="کاربر هم‌نام (سپنج)",
            role=RoleEnum.MANAGER
        )
        inactive_user = User(
            restaurant_id=kariz.id,
            branch_id=branch_enghelab.id,
            email="inactive@kariz.ir",
            hashed_password=pw_hash,
            full_name="پرسنل غیرفعال",
            role=RoleEnum.WAITER,
            is_active=False
        )
        unassigned_kitchen = User(
            restaurant_id=kariz.id,
            branch_id=branch_enghelab.id,
            station_id=None,
            email="unassigned.kitchen@kariz.ir",
            hashed_password=pw_hash,
            full_name="آشپز بدون ایستگاه",
            role=RoleEnum.KITCHEN
        )
        unassigned_waiter = User(
            restaurant_id=kariz.id,
            branch_id=None,
            email="unassigned.waiter@kariz.ir",
            hashed_password=pw_hash,
            full_name="سالن‌کار بدون شعبه",
            role=RoleEnum.WAITER
        )

        db.add_all([
            manager,
            waiter_enghelab,
            barista_enghelab,
            chef_enghelab,
            waiter_sanaee,
            waiter_shahrak,
            waiter_fereshteh,
            sepanj_manager,
            sepanj_waiter,
            duplicate_kariz,
            duplicate_sepanj,
            inactive_user,
            unassigned_kitchen,
            unassigned_waiter
        ])
        db.flush()


        # ----------------------------------------------------
        # 7. Menu Categories & Menu Items (Toman Pricing)
        # ----------------------------------------------------
        cat_espresso = MenuCategory(restaurant_id=kariz.id, name="اسپرسو بار", display_order=1)
        cat_brew = MenuCategory(restaurant_id=kariz.id, name="بار دمی و اسپشالتی", display_order=2)
        cat_cold = MenuCategory(restaurant_id=kariz.id, name="نوشیدنی‌های سرد و موکتل", display_order=3)
        cat_kitchen = MenuCategory(restaurant_id=kariz.id, name="بشقاب گرم و ساندویچ", display_order=4)
        cat_bakery = MenuCategory(restaurant_id=kariz.id, name="قنادی و بیکری", display_order=5)

        db.add_all([cat_espresso, cat_brew, cat_cold, cat_kitchen, cat_bakery])
        db.flush()

        # Items
        item_espresso = MenuItem(
            restaurant_id=kariz.id,
            category_id=cat_espresso.id,
            name_fa="اسپرسو دابل",
            name_en="Double Espresso",
            price_toman=85000,
            default_station_type=StationTypeEnum.BARISTA,
            description="ترکیب ۸۰/۲۰ عربیکا و روبوستا با کرمای غلیظ"
        )
        item_latte = MenuItem(
            restaurant_id=kariz.id,
            category_id=cat_espresso.id,
            name_fa="لاته آرت",
            name_en="Caffe Latte",
            price_toman=120000,
            default_station_type=StationTypeEnum.BARISTA,
            description="اسپرسو دابل، شیر بخاردیده و لایه‌ای از فوم مخملی"
        )
        item_cappuccino = MenuItem(
            restaurant_id=kariz.id,
            category_id=cat_espresso.id,
            name_fa="کاپوچینو ایتالیایی",
            name_en="Cappuccino",
            price_toman=115000,
            default_station_type=StationTypeEnum.BARISTA,
            description="نسبت کلاسیک یک‌سوم اسپرسو، شیر و فوم غلیظ"
        )
        item_chemex = MenuItem(
            restaurant_id=kariz.id,
            category_id=cat_brew.id,
            name_fa="کمکس کلمبیا هویلا",
            name_en="Chemex Colombia Huila",
            price_toman=165000,
            default_station_type=StationTypeEnum.BREW_BAR,
            description="عصاره‌گیری شفاف با نت‌های مرکباتی و ترشی دلنشین"
        )
        item_v60 = MenuItem(
            restaurant_id=kariz.id,
            category_id=cat_brew.id,
            name_fa="وی‌سی اتیوپی یرگاچف",
            name_en="V60 Ethiopia Yirgacheffe",
            price_toman=175000,
            default_station_type=StationTypeEnum.BREW_BAR,
            description="عطر گل یاس و تمشک با اسیدیته شفاف و ملایم"
        )
        item_mojito = MenuItem(
            restaurant_id=kariz.id,
            category_id=cat_cold.id,
            name_fa="رد موهیتو ترش و شیرین",
            name_en="Red Mojito",
            price_toman=145000,
            default_station_type=StationTypeEnum.COLD_BAR,
            description="سیروپ توت‌فرنگی، نعناع تازه، لیمو سنگی و آب سودا"
        )
        item_iced_latte = MenuItem(
            restaurant_id=kariz.id,
            category_id=cat_cold.id,
            name_fa="آیس لاته کارامل",
            name_en="Iced Caramel Latte",
            price_toman=135000,
            default_station_type=StationTypeEnum.COLD_BAR,
            description="اسپرسو سرد، شیر تازه، یخ و سیروپ کارامل نمکی"
        )
        item_roast_beef = MenuItem(
            restaurant_id=kariz.id,
            category_id=cat_kitchen.id,
            name_fa="ساندویچ رست بیف با پنیر گودا",
            name_en="Roast Beef Panini",
            price_toman=290000,
            default_station_type=StationTypeEnum.KITCHEN,
            description="گوشت گوساله مغزپخت ریش‌ریش، قارچ تفت‌داده و پنیر ذوب‌شده"
        )
        item_omelet = MenuItem(
            restaurant_id=kariz.id,
            category_id=cat_kitchen.id,
            name_fa="املت سنتی ایرانی با نان سنگک",
            name_en="Traditional Persian Omelet",
            price_toman=175000,
            default_station_type=StationTypeEnum.KITCHEN,
            description="گوجه تازه رنده‌شده با روغن حیوانی، تخم‌مرغ محلی و سبزی خوردن"
        )
        item_caesar = MenuItem(
            restaurant_id=kariz.id,
            category_id=cat_kitchen.id,
            name_fa="سالاد سزار با فیله مرغ گریل",
            name_en="Grilled Chicken Caesar Salad",
            price_toman=320000,
            default_station_type=StationTypeEnum.KITCHEN,
            description="کاهو رسمی پیچ، فیله مرغ مرینیت‌شده، پنیر پارمسان و سس خانگی سزار"
        )
        item_croissant = MenuItem(
            restaurant_id=kariz.id,
            category_id=cat_bakery.id,
            name_fa="کرواسان فرانسوی نوتلا",
            name_en="Nutella Croissant",
            price_toman=130000,
            default_station_type=StationTypeEnum.KITCHEN,
            description="کرواسان کره‌ای تازه پخت، مغز نوتلا خالص و فندق رست‌شده"
        )

        db.add_all([
            item_espresso,
            item_latte,
            item_cappuccino,
            item_chemex,
            item_v60,
            item_mojito,
            item_iced_latte,
            item_roast_beef,
            item_omelet,
            item_caesar,
            item_croissant
        ])
        db.flush()

        # ----------------------------------------------------
        # 8. Realistic Shift Orders & Concurrency Scenarios
        # ----------------------------------------------------
        now = utcnow()
        today_date = utcnow_date()

        # Scenario A: Completed Orders (Served) with realistic turnaround
        for i in range(1, 6):
            t_created = now - timedelta(minutes=60 + i * 15)
            t_ready = t_created + timedelta(minutes=10 + i * 2)
            t_served = t_ready + timedelta(minutes=2)

            ord_compl = Order(
                restaurant_id=kariz.id,
                branch_id=branch_enghelab.id,
                table_id=enghelab_tables[i - 1].id,
                waiter_id=waiter_enghelab.id,
                order_date=today_date,
                order_number=i,
                status=OrderStatusEnum.SERVED,
                version=2,
                notes="سفارش سرو شده موفق",
                total_price_toman=item_latte.price_toman + item_croissant.price_toman,
                created_at=t_created,
                updated_at=t_served,
                served_at=t_served
            )
            db.add(ord_compl)
            db.flush()

            it1 = OrderItem(
                restaurant_id=kariz.id,
                branch_id=branch_enghelab.id,
                order_id=ord_compl.id,
                menu_item_id=item_latte.id,
                station_id=enghelab_barista.id,
                quantity=1,
                unit_price_toman=item_latte.price_toman,
                status=OrderItemStatusEnum.SERVED,
                version=3,
                created_at=t_created,
                preparing_at=t_created + timedelta(minutes=1),
                ready_at=t_ready,
                served_at=t_served
            )
            it2 = OrderItem(
                restaurant_id=kariz.id,
                branch_id=branch_enghelab.id,
                order_id=ord_compl.id,
                menu_item_id=item_croissant.id,
                station_id=enghelab_kitchen.id,
                quantity=1,
                unit_price_toman=item_croissant.price_toman,
                status=OrderItemStatusEnum.SERVED,
                version=3,
                created_at=t_created,
                preparing_at=t_created + timedelta(minutes=2),
                ready_at=t_ready,
                served_at=t_served
            )
            db.add_all([it1, it2])

        # Scenario B: Active Order with Independent Stations (Barista READY, Kitchen PREPARING)
        t_active = now - timedelta(minutes=8)
        ord_active = Order(
            restaurant_id=kariz.id,
            branch_id=branch_enghelab.id,
            table_id=enghelab_tables[5].id,  # میز ۶
            waiter_id=waiter_enghelab.id,
            order_date=today_date,
            order_number=6,
            status=OrderStatusEnum.IN_PROGRESS,
            version=1,
            notes="لطفاً سس سزار جدا باشد",
            total_price_toman=item_cappuccino.price_toman + item_roast_beef.price_toman,
            created_at=t_active,
            updated_at=now
        )
        db.add(ord_active)
        db.flush()

        # Cappuccino is already READY at Barista!
        item_active_drink = OrderItem(
            restaurant_id=kariz.id,
            branch_id=branch_enghelab.id,
            order_id=ord_active.id,
            menu_item_id=item_cappuccino.id,
            station_id=enghelab_barista.id,
            quantity=1,
            unit_price_toman=item_cappuccino.price_toman,
            status=OrderItemStatusEnum.READY,
            version=2,
            modifiers="فوم زیاد، بدون دارچین",
            created_at=t_active,
            preparing_at=t_active + timedelta(minutes=1),
            ready_at=now - timedelta(minutes=2)
        )
        # Roast beef panini is still PREPARING at Kitchen!
        item_active_food = OrderItem(
            restaurant_id=kariz.id,
            branch_id=branch_enghelab.id,
            order_id=ord_active.id,
            menu_item_id=item_roast_beef.id,
            station_id=enghelab_kitchen.id,
            quantity=1,
            unit_price_toman=item_roast_beef.price_toman,
            status=OrderItemStatusEnum.PREPARING,
            version=2,
            modifiers="نان تست‌شده و برشته",
            created_at=t_active,
            preparing_at=t_active + timedelta(minutes=2)
        )
        db.add_all([item_active_drink, item_active_food])

        # Scenario C: Active Order with Bottleneck DELAY (Delayed Roast Beef Panini exceeding 15 min SLA)
        t_delayed = now - timedelta(minutes=24)
        ord_delayed = Order(
            restaurant_id=kariz.id,
            branch_id=branch_enghelab.id,
            table_id=enghelab_tables[6].id,  # میز ۷
            waiter_id=waiter_enghelab.id,
            order_date=today_date,
            order_number=7,
            status=OrderStatusEnum.IN_PROGRESS,
            version=1,
            notes="میز مشتری وی‌آی‌پی منتظر غذاست",
            total_price_toman=item_roast_beef.price_toman * 2 + item_mojito.price_toman,
            created_at=t_delayed,
            updated_at=now
        )
        db.add(ord_delayed)
        db.flush()

        item_delayed_mojito = OrderItem(
            restaurant_id=kariz.id,
            branch_id=branch_enghelab.id,
            order_id=ord_delayed.id,
            menu_item_id=item_mojito.id,
            station_id=enghelab_cold.id,
            quantity=1,
            unit_price_toman=item_mojito.price_toman,
            status=OrderItemStatusEnum.READY,
            version=2,
            created_at=t_delayed,
            preparing_at=t_delayed + timedelta(minutes=1),
            ready_at=t_delayed + timedelta(minutes=5)
        )
        item_delayed_beef = OrderItem(
            restaurant_id=kariz.id,
            branch_id=branch_enghelab.id,
            order_id=ord_delayed.id,
            menu_item_id=item_roast_beef.id,
            station_id=enghelab_kitchen.id,
            quantity=2,
            unit_price_toman=item_roast_beef.price_toman,
            status=OrderItemStatusEnum.PREPARING,
            version=2,
            modifiers="با پنیر دوبل",
            created_at=t_delayed,
            preparing_at=t_delayed + timedelta(minutes=2)  # Elapsed 22 min > SLA 15 min -> DELAYED!
        )
        db.add_all([item_delayed_mojito, item_delayed_beef])

        # Scenario D: Order Demonstrating Item Cancellation and Appended Item (Order version = 3)
        t_dyn = now - timedelta(minutes=15)
        ord_dynamic = Order(
            restaurant_id=kariz.id,
            branch_id=branch_enghelab.id,
            table_id=enghelab_tables[7].id,  # میز ۸
            waiter_id=waiter_enghelab.id,
            order_date=today_date,
            order_number=8,
            status=OrderStatusEnum.IN_PROGRESS,
            version=3,  # Incremented when new item was added
            notes="یک نوشیدنی بعداً اضافه شد",
            total_price_toman=item_caesar.price_toman + item_latte.price_toman,
            created_at=t_dyn,
            updated_at=now - timedelta(minutes=5)
        )
        db.add(ord_dynamic)
        db.flush()

        item_caesar_prep = OrderItem(
            restaurant_id=kariz.id,
            branch_id=branch_enghelab.id,
            order_id=ord_dynamic.id,
            menu_item_id=item_caesar.id,
            station_id=enghelab_kitchen.id,
            quantity=1,
            unit_price_toman=item_caesar.price_toman,
            status=OrderItemStatusEnum.PREPARING,
            version=2,
            created_at=t_dyn,
            preparing_at=t_dyn + timedelta(minutes=2)
        )
        item_croissant_cancelled = OrderItem(
            restaurant_id=kariz.id,
            branch_id=branch_enghelab.id,
            order_id=ord_dynamic.id,
            menu_item_id=item_croissant.id,
            station_id=enghelab_kitchen.id,
            quantity=1,
            unit_price_toman=item_croissant.price_toman,
            status=OrderItemStatusEnum.CANCELLED,
            version=2,
            modifiers="کنسل شده به درخواست مشتری",
            created_at=t_dyn
        )
        # Added dynamically 5 mins ago
        item_latte_appended = OrderItem(
            restaurant_id=kariz.id,
            branch_id=branch_enghelab.id,
            order_id=ord_dynamic.id,
            menu_item_id=item_latte.id,
            station_id=enghelab_barista.id,
            quantity=1,
            unit_price_toman=item_latte.price_toman,
            status=OrderItemStatusEnum.PENDING,
            version=1,
            modifiers="اضافه شده به سفارش اولیه",
            created_at=now - timedelta(minutes=5)
        )
        db.add_all([item_caesar_prep, item_croissant_cancelled, item_latte_appended])

        # Scenario E: Seed orders across the other 3 branches for realistic branch comparison
        # Sanaee Branch (Heavy Brew Bar)
        for i in range(1, 4):
            t_s = now - timedelta(minutes=30 + i * 10)
            ord_s = Order(
                restaurant_id=kariz.id,
                branch_id=branch_sanaee.id,
                table_id=sanaee_tables[i - 1].id,
                waiter_id=waiter_sanaee.id,
                order_date=today_date,
                order_number=i,
                status=OrderStatusEnum.SERVED,
                version=2,
                total_price_toman=item_chemex.price_toman,
                created_at=t_s,
                updated_at=t_s + timedelta(minutes=9),
                served_at=t_s + timedelta(minutes=9)
            )
            db.add(ord_s)
            db.flush()
            db.add(OrderItem(
                restaurant_id=kariz.id,
                branch_id=branch_sanaee.id,
                order_id=ord_s.id,
                menu_item_id=item_chemex.id,
                station_id=sanaee_stations[1].id,
                quantity=1,
                unit_price_toman=item_chemex.price_toman,
                status=OrderItemStatusEnum.SERVED,
                version=3,
                created_at=t_s,
                preparing_at=t_s + timedelta(minutes=1),
                ready_at=t_s + timedelta(minutes=8),
                served_at=t_s + timedelta(minutes=9)
            ))

        # Shahrak-e Gharb Branch (Large kitchen volume)
        for i in range(1, 5):
            t_sh = now - timedelta(minutes=45 + i * 12)
            ord_sh = Order(
                restaurant_id=kariz.id,
                branch_id=branch_shahrak.id,
                table_id=shahrak_tables[i - 1].id,
                waiter_id=waiter_shahrak.id,
                order_date=today_date,
                order_number=i,
                status=OrderStatusEnum.SERVED,
                version=2,
                total_price_toman=item_caesar.price_toman + item_roast_beef.price_toman,
                created_at=t_sh,
                updated_at=t_sh + timedelta(minutes=18),
                served_at=t_sh + timedelta(minutes=18)
            )
            db.add(ord_sh)
            db.flush()
            db.add(OrderItem(
                restaurant_id=kariz.id,
                branch_id=branch_shahrak.id,
                order_id=ord_sh.id,
                menu_item_id=item_roast_beef.id,
                station_id=shahrak_stations[3].id,
                quantity=1,
                unit_price_toman=item_roast_beef.price_toman,
                status=OrderItemStatusEnum.SERVED,
                version=3,
                created_at=t_sh,
                preparing_at=t_sh + timedelta(minutes=2),
                ready_at=t_sh + timedelta(minutes=16),
                served_at=t_sh + timedelta(minutes=18)
            ))

        # ----------------------------------------------------
        # 9. Seed BranchDailyCounters for Branches
        # ----------------------------------------------------
        db.add_all([
            BranchDailyCounter(
                restaurant_id=kariz.id,
                branch_id=branch_enghelab.id,
                counter_date=today_date,
                last_order_number=8
            ),
            BranchDailyCounter(
                restaurant_id=kariz.id,
                branch_id=branch_sanaee.id,
                counter_date=today_date,
                last_order_number=3
            ),
            BranchDailyCounter(
                restaurant_id=kariz.id,
                branch_id=branch_shahrak.id,
                counter_date=today_date,
                last_order_number=4
            ),
            BranchDailyCounter(
                restaurant_id=kariz.id,
                branch_id=branch_fereshteh.id,
                counter_date=today_date,
                last_order_number=0
            ),
            BranchDailyCounter(
                restaurant_id=sepanj.id,
                branch_id=branch_sepanj.id,
                counter_date=today_date,
                last_order_number=0
            ),
        ])

        # Commit all seeded data
        db.commit()


        print("[OK] Synthetic Demo Data successfully seeded!")
        print("-" * 60)
        print("Demo Credentials for Testing:")
        print("  - Manager (All branches): manager@kariz.ir / password123")
        print("  - Enghelab Waiter:       waiter.enghelab@kariz.ir / password123")
        print("  - Enghelab Barista:      barista.enghelab@kariz.ir / password123")
        print("  - Enghelab Kitchen Chef: chef.enghelab@kariz.ir / password123")
        print("  - Sanaee Waiter:         waiter.sanaee@kariz.ir / password123")
        print("  - Shahrak Waiter:        waiter.shahrak@kariz.ir / password123")
        print("  - Fereshteh Waiter:      waiter.fereshteh@kariz.ir / password123")
        print("  - Sepanj (Tenant B):     manager@sepanj.ir / password123")
        print("-" * 60)

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error during seeding: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
