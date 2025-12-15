import os
from dbfread import DBF
import pandas as pd
from werkzeug.security import generate_password_hash

def create_database(app, db):
    from .models import User, Organization, Plan, Ticket, Unit, Direction, Indicator, EconExec, EconMeasure
    with app.app_context():
        # db.drop_all()
        db.create_all()
        add_data_in_db(db)
        
def is_db_empty():
    from .models import User, Organization, Plan, Ticket, Ticket, Unit, Direction, Indicator, EconExec, EconMeasure
    return all([
        User.query.count() == 0,
        Organization.query.count() == 0,
        Plan.query.count() == 0,
        Ticket.query.count() == 0,
        Unit.query.count() == 0,
        Indicator.query.count() == 0,
        Unit.query.count() == 0,
    ])
        
def read_dbf(file_path, columns):
    data = []
    for record in DBF(file_path):
        row = {col: record[col] for col in columns}
        data.append(row)
    return data      
        
def add_data_in_db(db):
    if is_db_empty():
        from .models import User, Organization, Unit, Direction, Indicator, Ministry
        from sqlalchemy.exc import IntegrityError
        print('Filling is in progress...')
        
        ### ORGANIZATION DATA ###
        website_path = os.path.dirname(os.path.abspath(__file__))
    
        Brest_org_data_path = os.path.join(website_path, 'static/files/organizations', 'Брест.dbf')
        Vitebsk_org_data_path = os.path.join(website_path, 'static/files/organizations', 'Витебск.dbf')
        Gomel_org_data_path = os.path.join(website_path, 'static/files/organizations', 'Гомель.dbf')
        Grodno_org_data_path = os.path.join(website_path, 'static/files/organizations', 'Гродно.dbf')
        Minsk_org_data_path = os.path.join(website_path, 'static/files/organizations', 'Минск.dbf')
        MinskRegion_org_data_path = os.path.join(website_path, 'static/files/organizations', 'Минск_область.dbf')
        Migilev_org_data_path = os.path.join(website_path, 'static/files/organizations', 'Могилев.dbf')

        columns_org = ['OKPO', 'NAME', 'MIN', 'UNP']

        Brest_org_data = read_dbf(Brest_org_data_path, columns_org)
        Vitebsk_org_data = read_dbf(Vitebsk_org_data_path, columns_org)
        Gomel_org_data = read_dbf(Gomel_org_data_path, columns_org)
        Grodno_org_data = read_dbf(Grodno_org_data_path, columns_org)
        Minsk_org_data = read_dbf(Minsk_org_data_path, columns_org)
        MinskRegion_org_data = read_dbf(MinskRegion_org_data_path, columns_org)
        Migilev_org_data = read_dbf(Migilev_org_data_path, columns_org)

        city_all_data = pd.concat([
            pd.DataFrame(Brest_org_data, columns=columns_org),
            pd.DataFrame(Vitebsk_org_data, columns=columns_org),
            pd.DataFrame(Gomel_org_data, columns=columns_org),
            pd.DataFrame(Grodno_org_data, columns=columns_org),
            pd.DataFrame(Minsk_org_data, columns=columns_org),
            pd.DataFrame(MinskRegion_org_data, columns=columns_org),
            pd.DataFrame(Migilev_org_data, columns=columns_org)
        ], ignore_index=True)

        MinskRegion_min_data_path = os.path.join(website_path, 'static/files/ministerstvo', 'MinskReg_min.dbf')
        columns_min = ['MIN', 'NAME']
        MinskRegion_min_data = read_dbf(MinskRegion_min_data_path, columns_min)

        min_all_data = pd.DataFrame(MinskRegion_min_data, columns=columns_min)

        ministries_dict = {}

        for _, row in min_all_data.drop_duplicates('MIN').iterrows():
            ministry = Ministry.query.filter_by(id=row['MIN']).first()
            
            if not ministry:
                ministry = Ministry(
                    id=row['MIN'],
                    name=row['NAME']
                )
                db.session.add(ministry)
            
            ministries_dict[row['MIN']] = ministry

        db.session.commit()

        for _, row in city_all_data.iterrows():
            organization_name = ' '.join(filter(None, [
                row['NAME']
            ]))
            
            existing_org = Organization.query.filter_by(okpo=row['OKPO']).first()
            
            if not existing_org:
                organization = Organization(
                    okpo=row['OKPO'],
                    name=organization_name,
                    ministry_id=row['MIN'], 
                    ynp=row['UNP']
                )
                db.session.add(organization)

        try:
            db.session.commit()
            print("Данные успешно добавлены в базу данных")
        except IntegrityError as e:
            db.session.rollback()
            print(f"Ошибка целостности данных: {e}")
        except Exception as e:
            db.session.rollback()
            print(f"Произошла ошибка: {e}")

        dop_org_data = [
            ('Брестское областное управление', '100000001000'),
            ('Витебское областное управление', '200000002000'),
            ('Гомельское областное управление', '300000003000'),
            ('Гродненское областное управление', '400000004000'),
            ('Управление г. Минск', '500000005000'),
            ('Минское областное управление', '600000006000'),
            ('Могилевское областное управление', '700000007000'),
            ('Департамент по энергоэффективности', '800000008000'),
        ]

        for name, okpo in dop_org_data:
            dop_org = Organization(name=name, okpo=str(okpo)) 
            db.session.add(dop_org)

        db.session.commit()
        ### ----------- ###

        ### USER DATA ###
        users_data = [
            ('Инженер-программист', os.getenv('adminemail1'), os.getenv('adminname1'), os.getenv('adminsecondname1'), os.getenv('adminpatr1'), os.getenv('adminphone1'), True, False, 14),
            ('Администратор', os.getenv('adminemail2'), os.getenv('adminname2'), os.getenv('adminsecondname2'), os.getenv('adminpatr2'), os.getenv('adminphone2'), True, False, 6471),
            ('Аудитор', os.getenv('auditoremailBrest'), 'Иванов1', 'Иван', 'Иванович', '+375445544431', False, True, 7940),
            ('Аудитор', os.getenv('auditoremailVitebsk'), 'Иванов2', 'Иван', 'Иванович', '+375445544432', False, True, 7941),
            ('Аудитор', os.getenv('auditoremailGomel'), 'Иванов3', 'Иван', 'Иванович', '+375445544433', False, True, 7942),
            ('Аудитор', os.getenv('auditoremailGrodno'), 'Иванов4', 'Иван', 'Иванович', '+375445544434', False, True, 7943),
            ('Аудитор', os.getenv('auditoremailMinskobl'), 'Иванов5', 'Иван', 'Иванович', '+375445544435', False, True, 7945),
            ('Аудитор', os.getenv('auditoremailMogilev'), 'Иванов6', 'Иван', 'Иванович', '+375445544436', False, True, 7946),
            ('Аудитор', os.getenv('auditoremailMinsk'), 'Иванов7', 'Иван', 'Иванович', '+375445544437', False, True, 7944),
            ('Аудитор', os.getenv('auditoremailNadzor'), 'Иванов8', 'Иван', 'Иванович', '+375445544438', False, True, 7947),
        ]

        for post, email, first_name, last_name, patronymic_name, phone, is_admin, is_auditor, organization_id in users_data:
            user = User(
                post = post,
                email=email,
                first_name=first_name,
                last_name=last_name,
                patronymic_name=patronymic_name,
                phone=phone,
                is_admin=is_admin,
                is_auditor=is_auditor,
                organization_id = organization_id,
                password=generate_password_hash(os.getenv('userpass'))
            )
            db.session.add(user)
        db.session.commit()
        ### ----------- ###
        
        ### Unit DATA ###
        unit_data = [
            (1, 'т.у.т.', 'т.у.т.'),
            (2, 'тонн', 'тонн'),
            (3, 'тыс. куб. м', 'тыс. куб. м'),
            (4, 'т. усл. влажн.', 'т. усл. влажн.'),
            (5, 'пл. куб. м', 'пл. куб. м'),
            (6, 'тыс. кВт · ч', 'тыс. кВт · ч'),
            (7, 'Гкал', 'Гкал'),
            (8, 'шт.', 'шт.'),
            (9, 'ед.', 'ед.'),
            (10, 'киловатт', 'киловатт'),
            (11, 'Гкал/ч', 'Гкал/ч'),
            (12, 'пог.м', 'пог.м'),
            (13, 'кв. м', 'кв. м'),
            (14, 'м2', 'м2'),
            (15, 'Мвт', 'Мвт')
        ]
        for id, code, name in unit_data:
            unit = Unit(
                id = id,
                code=code,
                name=name
            )
            db.session.add(unit)
        db.session.commit()
        ### ----------- ###   
        
        ### Direction DATA ###
        direction_data = [
            (1, '2', 'Коды, не относящиеся к основным направлениям', False),
            (8, '307', 'Другие мероприятия по повышению эффективности работы котельных и технологических печей', False),
            (9, '1001', 'Внедрение в производство современных энергоэффективных и повышение энергоэффективности действующих технологий и процессов', False),
            (8, '1002', 'Внедрение в производство современного энергоэффективного оборудования и материалов', False),
            (10, '1011', 'Ввод в эксплуатацию электрогенерирующего оборудования на основе паро- и газотурбинных, парогазовых, турбодетандерных и газопоршневых установок', False),
            (11, '1012', 'Передача тепловых нагрузок от ведомственных котельных на теплоэлектроцентрали', False),
            (8, '1013', 'Замена неэкономичных котлов и печей с низким коэффициентом полезного действия на более эффективные', False),
            (8, '1014', 'Замена газогорелочных устройств на энергоэффективные', False),
            (8, '1015', 'Внедрение устройств предотвращения накипеобразования на поверхностях нагрева котлов и другого оборудования (магнитно-импульсные и другие)', False),
            (8, '1016', 'Перевод котлов с жидких видов топлива на газ', False),
            (8, '1017', 'Внедрение котлов малой мощности вместо незагруженных котлов большой мощности', False),
            (8, '1018', 'Внедрение автоматизации процессов горения топлива в котлоагрегатах и другом топливоиспользующем оборудовании', False),
            (9, '1019', 'Использование возврата конденсата для нужд котельных', False),
            (8, '1020', 'Перевод паровых котлов в водогрейный режим', False),
            (8, '1021', 'Реконструкция (модернизация) энергоисточников с переводом в автоматический режим работы', False),
            (9, '1099', 'Другие мероприятия по повышению эффективности работы котельных', False),
            (9, '1100', 'Автоматизация технологических процессов, внедрение автоматизированной системы управления "Энергоэффективность"', False),
            (12, '1111', 'Децентрализация теплоснабжения с ликвидацией длинных и незагруженных паро- и теплотрасс', False),
            (12, '1112', 'Замена изношенных теплотрасс с внедрением эффективных трубопроводов (предварительно изолированных труб)', False),
            (8, '1113', 'Внедрение индивидуальных тепловых пунктов вместо центральных тепловых пунктов', False),
            (12, '1114', 'Модернизация тепловой изоляции паропроводов, системы отопления, горячего водоснабжения, запорной арматуры', False),
            (9, '1115', 'Установка теплоотражающих экранов за радиаторами отопления', False),
            (9, '1116', 'Модернизация теплоиспользующего оборудования', False),
            (9, '1199', 'Другие мероприятия по оптимизации теплоснабжения', False),
            (8, '1200', 'Ликвидация электронагрева с переводом технологического оборудования на современные высокоэкономичные энергоносители (природный газ, высокотемпературные жидкости и другие)', False),
            (8, '1211', 'Замена насосного оборудования более энергоэффективным', False),
            (8, '1212', 'Замена насосного оборудования в котельных на энергосберегающее меньшей мощности', False),
            (8, '1213', 'Замена насосного оборудования в системах водопроводно-канализационного хозяйства на энергосберегающее', False),
            (8, '1214', 'Замена повысительных, центробежных насосов  на энергосберегающие', False),
            (8, '1219', 'Другие мероприятия по замене насосного оборудования более энергоэффективным', False),
            (8, '1221', 'Внедрение энергоэффективного вентиляционного оборудования', False),
            (8, '1222', 'Децентрализация воздухоснабжения с установкой локальных компрессоров', False),
            (8, '1223', 'Децентрализация систем удаления отработанного воздуха с установкой локальных отсосов', False),
            (8, '1224', 'Децентрализация холодоснабжения с установкой локальных холодильных установок', False),
            (13, '1301', 'Термореновация ограждающих конструкций зданий, сооружений, жилищного фонда', False),
            (13, '1302', 'Замена оконных блоков и входных групп с установкой стеклопакетов', False),
            (9, '1311', 'Внедрение в производство современных энергоэффективных технологий', False),
            (9, '1312', 'Внедрение в производство современных энергоэффективных процессов', False),
            (9, '1313', 'Повышение энергоэффективности действующих технологий', False),
            (9, '1314', 'Повышение энергоэффективности действующих процессов', False),
            (9, '1315', 'Повышение энергоэффективности технологического оборудования', False),
            (9, '1316', 'Внедрение в производство современного энергоэффективного оборудования', False),
            (9, '1317', 'Внедрение в производство современных энергоэффективных материалов', False),
            (8, '1321', 'Замена морально устаревших теплообменников на более эффективные', False),
            (14, '1322', 'Модернизация изоляции теплообменников', False),
            (8, '1330', 'Внедрение энергоэффективных компрессоров с частотно-регулируемым электроприводом', False),
            (8, '1340', 'Замена нагревательного оборудования в пищеблоках, прачечных на энергоэффективное', False),
            (8, '1411', 'Внедрение в производство современного энергоэффективного оборудования с увеличением использования электрической энергии и с замещением углеводородного топлива', False),
            (8, '1412', 'Ввод новых электрокотлов', False),
            (8, '1413', 'Реконструкция (модернизация) энергоисточников с переводом на использование электронагрева', False),
            (9, '1419', 'Другие мероприятия, направленные на сокращение использования углеводородного топлива и увеличение использования электрической энергии', False),
            (9, '1421', 'Автоматизация и роботизация технологических процессов', False),
            (9, '1422', 'Внедрение автоматизированной системы управления потреблением энергоресурсов', False),
            (9, '1423', 'Мероприятия, направленные на снижение расхода электрической энергии на транспорт в электросетях', False),
            (8, '1424', 'Внедрение автоматических систем компенсации реактивной мощности', False),
            (8, '1425', 'Внедрение приборов автоматического регулирования в системах тепло-, газо-, и водоснабжения', False),
            (8, '1426', 'Внедрение частотно-регулируемых электроприводов на механизмах с переменной нагрузкой (сетевые теплофикационные насосные, канализационные насосные станции, системы водоснабжения, тягодутьевые механизмы котлов и другие)', False),
            (9, '1429', 'Другие мероприятия, направленные на автоматизацию  процессов в системах энерго-, газо- и водоснабжения', False),
            (8, '1500', 'Внедрение автоматических систем управления освещением, энергоэффективных осветительных устройств, секционного разделения освещения', False),
            (8, '1502', 'Внедрение энергоэффективных осветительных устройств, секционного разделения освещения', False),
            (14, '1511', 'Термореновация ограждающих конструкций зданий, сооружений', False),
            (14, '1512', 'Термореновация ограждающих конструкций кровли, подвалов', False),
            (14, '1513', 'Применение энергоэффективных материалов при модернизации тепловой изоляции промышленных установок и оборудования  (котлоагрегатов, холодильников, теплиц, трубопроводов и др.)', False),
            (8, '1514', 'Внедрение инфракрасных излучателей для локального обогрева рабочих мест и в технологических процессах', False),
            (14, '1515', 'Замена оконных блоков с установкой стеклопакетов и входных групп', False),
            (9, '1521', 'Внедрение автоматических систем управления освещением', False),
            (9, '1522', 'Внедрение секционного разделения освещения', False),
            (8, '1523', 'Внедрение энергоэффективных светильников уличного освещения', False),
            (8, '1524', 'Внедрение энергоэффективных ламп в светильниках уличного освещения', False),
            (8, '1525', 'Внедрение энергоэффективных светильников внутреннего освещения', False),
            (8, '1526', 'Внедрение энергоэффективных ламп в светильниках внутреннего освещения', False),
            (15, '1601', 'Ввод теплоэлектроцентралей, работающих на местных топливно-энергетических ресурсах', False),
            (8, '1602', 'Ввод новых котлов и другого топливоиспользующего оборудования, работающего на местных топливно-энергетических ресурсах', False),
            (8, '1603', 'Перевод котлов и другого топливоиспользующего оборудования на использование местных топливно-энергетических ресурсов', False),
            (8, '1606', 'Ввод энергогенерирующего и технологического оборудования, работающего с использованием отходов производства', False),
            (8, '1607', 'Внедрение мероприятий по увеличению использования энергии воды, ветра, солнца, геотермальных источников', False),
            (9, '1609', 'Другие мероприятия по увеличению использования местных топливно-энергетических ресурсов', False),
            (11, '1610', 'Ввод теплоэлектроцентралей, работающих на местных топливно-энергетических ресурсах', True),
            (8, '1621', 'Ввод новых котлов и другого топливоиспользующего оборудования, работающего на топливной щепе', True),
            (8, '1622', 'Ввод новых котлов и другого топливоиспользующего оборудования, работающего на древесных пеллетах (гранулах, брикетах)', True),
            (8, '1623', 'Ввод новых котлов и другого топливоиспользующего оборудования, работающего на отходах деревообработки, лесозаготовок, сельскохозяйственной деятельности', True),
            (8, '1624', 'Ввод новых котлов и другого топливоиспользующего оборудования, работающего на торфяном топливе', True),
            (8, '1625', 'Ввод новых котлов и другого топливоиспользующего оборудования, работающего на твердых коммунальных отходах, включая RDF-топливо', True),
            (8, '1626', 'Ввод новых котлов и другого топливоиспользующего оборудования, работающего на прочих местных топливно-энергетических ресурсов', True),
            (8, '1631', 'Ввод энергогенерирующего и технологического оборудования, работающего с использованием отходов деревообработки и лесозаготовок', True),
            (8, '1632', 'Ввод энергогенерирующего и технологического оборудования, работающего с использованием отходов сельскохозяйственной деятельности', True),
            (8, '1641', 'Реконструкция (модернизация) энергоисточников с переводом на использование топливной щепы', True),
            (8, '1642', 'Реконструкция (модернизация) энергоисточников с переводом на использование древесных пеллетов (гранул, брикетов)', True),
            (8, '1643', 'Реконструкция (модернизация) энергоисточников с переводом на использование отходов деревообработки, лесозаготовок, сельскохозяйственной деятельности', True),
            (8, '1644', 'Реконструкция (модернизация) энергоисточников с переводом на использование торфяного топлива', True),
            (8, '1645', 'Реконструкция (модернизация) энергоисточников с переводом на использование прочих местных топливно-энергетических ресурсов', True),
            (8, '1651', 'Внедрение мероприятий по увеличению использования энергии воды', True),
            (8, '1652', 'Внедрение мероприятий по увеличению использования энергии ветра', True),
            (8, '1653', 'Внедрение мероприятий по увеличению использования энергии солнца', True),
            (8, '1654', 'Внедрение мероприятий по увеличению использования геотермальных источников энергии', True),
            (8, '1655', 'Внедрение мероприятий по установке тепловых насосов, использующих энергию из окружающей среды', True),
            (8, '1656', 'Внедрение биогазовых установок', True),
            (9, '1699', 'Другие мероприятия по увеличению использования местных топливно-энергетических ресурсов', True),
            (8, '1710', 'Утилизация тепловых вторичных энергетических ресурсов', False),
            (8, '1721', 'Внедрение тепловых насосов компрессорного типа в системах теплоснабжения и холодоснабжения', False),
            (8, '1722', 'Установка абсорбционных бромисто-литиевых тепловых насосов в системах теплоснабжения и холодоснабжения', False),
            (8, '1800', 'Утилизация тепловых возобновляемых энергетических ресурсов', False),
            (8, '1801', 'Ввод энергогенерирующего и технологического оборудования, работающего с использованием возобновляемых энергетических ресурсов избыточного давления', False),
            (8, '1810', 'Ввод энергогенерирующего и технологического оборудования, работающего с использованием вторичных энергетических ресурсов избыточного давления', False),
            (9, '1900', 'Прочие мероприятия по повышению эффективности использования топливно-энергетических ресурсов', False)
        ]
        
        for id_unit, code, name, is_local in direction_data:
            direction = Direction(
                id_unit = id_unit,
                code=code,
                name=name,
                is_local=is_local
            )
            db.session.add(direction)
        db.session.commit()  
        # ### ----------- ###      
        
        
        ### Indicator DATA ###
        indicator_data = [
            (1, 1, '1000', 'Котельно-печное топливо израсходовано всего, в том числе', 1.000, True, True, False, False, False, False, 1, 10, None, None, None),
            (2, 2, '1040', 'Топливо печное бытовое', 1.450, False, False, False, False, False, False, 1, 20, None, None, 1),
            (3, 2, '1050', 'Мазут топочный', 1.370, False, False, False, False, False, False, 1, 30, None, None, 1),
            (4, 2, '1060', 'Газы углеводородные нефтепереработки', 1.500, False, False, False, False, False, False, 1, 40, None, None, 1),
            (5, 3, '1090', 'Газ природный', 1.150, False, False, False, False, False, False, 1, 50, None, None, 1),
            (6, 3, '1110', 'Газ природный попутный', 1.300, False, False, False, False, True, False, 1, 60, None, None, 1),
            (7, 2, '1150', 'Газы углеводородные сжиженные', 1.570, False, False, False, False, False, False, 1, 70, None, None, 1),
            (8, 2, '1160', 'Уголь и продукты переработки угля', 1.000, False, False, False, False, False, False, 1, 80, None, None, 1),
            (9, 4, '1620', 'Торф топливный фрезерный', 0.340, False, False, False, False, True, False, 1, 90, None, None, 1),
            (10, 4, '1630', 'Торф топливный кусковой', 0.410, False, False, False, False, True, False, 1, 100, None, None, 1),
            (11, 4, '1640', 'Брикеты и полубрикеты торфяные', 0.600, False, False, False, False, True, False, 1, 110, None, None, 1),
            (12, 2, '1660', 'Кокс металлургический, коксик и коксовая мелочь', 0.990, False, False, False, False, False, False, 1, 120, None, None, 1),
            (13, 5, '1680', 'Щепа топливная', 0.187, False, False, False, False, True, True, 1, 130, None, None, 1),
            (14, 5, '1690', 'Дрова', 0.266, False, False, False, False, True, True, 1, 140, None, None, 1),
            (15, 1, '1700', 'Прочие виды топлива - всего', 1.000, False, False, False, False, False, True, 1, 150, None, None, 1),
            (16, 1, '1720', 'нефть сырая', 1.000, False, False, False, False, False, False, 1, 160, None, None, 1),
            (17, 1, '1730', 'отходы лесозаготовок и деревообработки', 1.000, False, False, False, False, True, True, 1, 170, None, None, 1),
            (18, 1, '1740', 'отходы с/х деятельности и прочие виды природного топлива', 1.000, False, False, False, False, True, True, 1, 180, None, None, 1),
            (19, 1, '1741', 'древесный уголь', 1.000, False, False, False, False, False, False, 1, 190, None, None, 1),
            (20, 1, '1742', 'древесные гранулы, пеллеты', 1.000, False, False, False, False, True, True, 1, 200, None, None, 1),
            (21, 1, '1743', 'торфодревесное топливо', 1.000, False, False, False, False, True, False, 1, 210, None, None, 1),
            (22, 1, '1745', 'биогаз', 1.000, False, False, False, False, True, True, 1, 220, None, None, 1),
            (23, 1, '1750', 'метано-водородная фракция', 1.000, False, False, False, False, False, False, 1, 230, None, None, 1),
            (24, 1, '1760', 'лигнин гидролизного производства', 1.000, False, False, False, False, False, False, 1, 240, None, None, 1),
            (25, 1, '1770', 'Х-масла производства капролактама', 1.000, False, False, False, False, False, False, 1, 250, None, None, 1),
            (26, 1, '1771', 'смесь эфиров и кислот', 1.000, False, False, False, False, False, False, 1, 260, None, None, 1),
            (27, 1, '1772', 'метанольная фракция', 1.000, False, False, False, False, False, False, 1, 270, None, None, 1),
            (28, 1, '1780', 'сульфатные и сульфитные щелока целлюлозно-бумажной промышленности', 1.000, False, False, False, False, False, False, 1, 280, None, None, 1),
            (29, 1, '1791', 'нефтешлам', 1.000, False, False, False, False, True, False, 1, 290, None, None, 1),
            (30, 1, '1793', 'адсорбированные отходы после очистных сооружений', 1.000, False, False, False, False, True, False, 1, 300, None, None, 1),
            (31, 1, '1794', 'использованные автопокрышки', 1.000, False, False, False, False, True, False, 1, 310, None, None, 1),
            (32, 1, '1795', 'прочие горючие отходы', 1.000, False, False, False, False, True, False, 1, 320, None, None, 1),
            (33, 6, '1105', 'Электроэнергия израсходовано всего', 0.123, True, False, True, False, False, False, 2, 330, None, None, None),
            (34, 6, '1405', 'Электроэнергия, выработанная собственными энергоисточниками, в том числе', 0.123, True, False, True, True, False, False, 2, 340, None, None, 33),
            (35, 6, '1425', 'энергия воды, ветра, солнца, геотермальных источников', 0.123, True, False, True, False, True, False, 2, 350, None, None, 34),
            (36, 6, '1445', 'собственная выработка электроэнергии на АЭС', 0.123, True, False, True, False, False, False, 2, 360, None, None, 34),
            (37, 7, '1104', 'Теплоэнергия израсходовано всего', 0.143, True, False, True, False, False, False, 3, 370, None, None, None),
            (38, 7, '1404', 'Теплоэнергия, произведенная собственными энергоисточниками,  в том числе', 0.143, True, False, True, True, False, False, 3, 380, None, None, 37),
            (39, 7, '1424', 'энергия воды, ветра, солнца, геотермальных источников', 0.143, True, False, True, False, True, False, 3, 390, None, None, 38),
            (40, 1, '260', 'Суммарное потребление ТЭР', 1.000, True, True, False, False, False, False, 4, 400, None, None, None),
            (41, 1, '9900', 'Ожидаемая экономия ТЭР от внедрения мероприятий в текущем году', 1.000, True, True, False, False, False, False, 5, 410, None, None, None),
            (42, 1, '9910', 'Экономия ТЭР от мероприятий предыдущего года внедрения, в том числе:', 1.000, True, False, False, False, False, False, 6, 420, None, None, None),
            (43, 1, '9911', 'январь-март', 1.000, True, False, False, False, False, False, 6, 430, None, None, 42),
            (44, 1, '9912', 'январь-июнь', 1.000, True, False, False, False, False, False, 6, 440, None, None, 42),
            (45, 1, '9913', 'январь-сентябрь', 1.000, True, False, False, False, False, False, 6, 450, None, None, 42),
            (46, 1, '9914', 'январь-декабрь', 1.000, True, False, False, False, False, False, 6, 460, None, None, 42),
            (47, 1, '9999', 'Итого: годовая экономия ТЭР от энергосберегающих мероприятий', 1.000, True, True, False, False, False, False, 7, 470, None, None, None)
        ]
        
        from decimal import Decimal, InvalidOperation
        def to_decimal_3(value):
            try:
                return Decimal(value).quantize(Decimal('0.001'))
            except (InvalidOperation, TypeError, ValueError):
                return Decimal('0.000')

        for IdIndicator, IdUnit, CodeIndicator, NameIndicator, CoeffToTut, IsMandatory, IsSummary, IsSendRealUnit, IsSelfProd, IsLocal, IsRenewable, Group, RowN, DateStart, DateEnd, IdIndicatorParent in indicator_data:
            indicator = Indicator(
                id=IdIndicator,
                id_unit=IdUnit,
                code=CodeIndicator,
                name=NameIndicator,
                CoeffToTut=to_decimal_3(CoeffToTut),
                IsMandatory=IsMandatory,
                IsSummary=IsSummary,
                IsSendRealUnit=IsSendRealUnit,
                IsSelfProd=IsSelfProd,
                IsLocal=IsLocal,
                IsRenewable=IsRenewable,
                Group=Group,
                RowN=RowN,
                DateStart=DateStart,
                DateEnd=DateEnd,
                id_indicator_parent=IdIndicatorParent
            )
            db.session.add(indicator)
        db.session.commit()
        ### ----------- ###   
    
    
        print('The filling is finished!')
    else:
        print('The database already contains the data!')