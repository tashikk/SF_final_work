import pandas as pd
import numpy as np
from statistics import mean
import re

def replace_property(row):
    
    if row in ['single-family home','Single Family Home','Single Family']:
        return 'single family home'
    elif row == 'Condo':
        return 'condo'
    elif row in ['Townhouse', 'Townhome']:
        return 'townhouse'
    elif row in ['Multi-Family Home','multi-family','Multi Family','Multi-Family']:
        return 'multi family home'
    elif row in ['1 Story','One Story']:
        return '1 story'
    elif row in ['2 Stories', '2 Story', 'Two Story']:
        return '2 stories'
    elif row in ['mobile/manufactured', 'Mfd/Mobile Home', 'Mobile / Manufactured']:
        return 'mobile/manufactured'
    elif row in ['Cooperative', 'coop']:
        return 'cooperative'
    elif row in ['Apartment', 'apartment']:
        return 'apartment'
    elif row in ['lot/land', 'Land']:
        return 'land'
    elif row in ['Other Style', 'Other']:
        return 'other style'
    else:
        return row

def make_baths_count(row):
    row = str(row)
    row = row.replace('Bathrooms: ', '').replace(' Baths', '').replace(' ba', '').replace(',','.')
    try:
        if row != 'nan':
            return float(row)
        else:
            return 0
    except:
        return 0

def make_beds_count(row):
    row = str(row)
    if row.find(' Beds') > -1:
        try:
            return int(row.replace(' Beds', ''))
        except: #если указано что-то другое #1-2
            return 1
    elif row.find(' bd') >-1:
        try:
            return int(row.replace(' bd', ''))
        except: #если указано что-то другое #--
            return 0
    else: 
        try:
            return int(row)
        except:
            return 0

def make_beds_square(row): #переводим в квадратные метры
    row = str(row)
    if row.find(' sqft') > -1:
        try:
            return float(row.replace(' sqft', '').replace(',',''))*0.093
        except: 
            return 0
    elif row.find(' acres') > -1:
        try:
            return float(row.replace(' acres', '').replace(',',''))*4046.86
        except: 
            return 0
    else:
        return 0

def make_schools(row):

    #разбираем, какие классы есть в близлежащих школах
    grades = eval(row[1:-1])['data']['Grades']
    
    result={'K':0,'1':0,'2':0,'3':0,'4':0,'5':0,'6':0,'7':0,'8':0,'9':0,'10':0,'11':0,'12':0, 'PK':0}
    for i in grades:
        i = (str(i).replace(' to ', '-').replace('–', '-')).split(',')
        for ii in i:
            ii = ii.strip().upper().replace('PK','PRESCHOOL')
            if 'PRESCHOOL' in ii:
                result['PK']+=1
                ii = ii.replace('PRESCHOOL','1')
            if 'K' in ii:
                result['K']+=1
                ii = ii.replace('K','1')
            if '-' in ii:
                j = ii.split('-')
                for k in range(int(j[0]), int(j[1])+1):
                    result[str(k)]+=1
    
    #считаем количество школ 
    result['schools_count']=len(eval(row[1:-1])['rating'])
    
    #считаем дистанцию по школам
    result['min_dist']=0
    result['max_dist']=0
    result['mean_dist']=0

    data_list = eval(row[1:-1])['data']['Distance']
    dist_list=[]
    for i in data_list:
        i = i.replace('mi', '').strip()
        try:
            i = float(i)
            dist_list.append(i)
        except:
            print(i)
            i = 0 
    if len(dist_list)>0:
        result['min_dist']=min(dist_list)
        result['max_dist']=max(dist_list)
        result['mean_dist']=mean(dist_list)
    
    #разбираем рейтинги школ
    regex = re.compile('\D+')
    data2_list = eval(row[1:-1])['rating']
    rate_list=[]
    if len(data2_list)>0:
        for i in data2_list:
            i = i.replace('/10','')
            i = regex.sub('', str(i))
            if i != '':
                rate_list.append(int(i))
            else:
                rate_list.append(0)
    if len(rate_list)>0:
        result['max_rate'] = max(rate_list) 
    else:
        result['max_rate']=0
        
    if len(dist_list)==len(rate_list):
        result['average_rate_school']=np.array(dist_list)@np.array(rate_list)
    else:
        result['average_rate_school']=0
    
    return pd.Series(result)

def make_stories(row):
    regex_sq = re.compile('\D+')
    try:
        row=float(row)
    except:
        row=regex_sq.sub('', str(row))
        if row != '':
            row = float(row)
        else:
            row = 1
    return row

def make_facts(row, columns):
    fact_dict = {}
    for i in columns:
        fact_dict[i]=float('nan')
    row = eval(row)['atAGlanceFacts']
    for i in row:
        fact_dict[i['factLabel']]=i['factValue']
    return pd.Series(fact_dict)

#в цене за кв. фут избавляемся от всяких лишних знаков, переводим в целое число
def make_price(row):
    row = str(row).replace('$','').replace('/sqft','').replace(' / Sq. Ft.', '').replace(',','')
    try:
        row = int(row)
    except:
        if row in ['None', 'No Info', 'No Data', '', 'Contact manager']:
            row = 0
        else:
            row = 0
    return row

#в размере лота убираем лишние знаки, переводим все в единые единицы измерения
def make_lot(row):
    row1 = row
    row = str(row).replace('$','').replace(' sqft lot','').replace(' Sq. Ft.', '').replace(' sqft', '').replace(',','')
    try:
        row = float(row)
    except:
        if row.lower().find('acre') >-1:
            row = row.lower().replace(' lot', '').replace(' acres', '').replace(' acre', '').replace(' acres', '')
        try:
            row = float(row) * 43560.04
        except:
            if row in ['None', 'No Info', 'No Data', '', 'Contact manager', '--', '—']:
                row = 0
            else:
                print(row, '->', row1)
    return row

#на вход у нас строка в виде Series
#на выходе должны быть такие колонки
#Index(['new_id', 'Remodeled', 'mean_dist', '9', 'schools_count', 'min_dist',
#       'prop_type', '7', 'beds_square', 'Parking', 'sqft', 'zipcode_int', '6',
#       '5', 'Cooling', 'beds_count', 'pool', 'lot', 'state_encoding',
#       'baths_count', 'K', 'average_rate_school', 'city_hash', 'max_dist',
#       'street_hash', 'price_sqft', 'stories_count', 'Year', 'PK', 'price_lot',
#       '12', 'max_rate', 'address_hash', 'price', 'state_mean', '8']
def make_data_4_predict(stroka, states_list,mean_target):
    data = pd.DataFrame(stroka).T
    
    #1
    if data['state'].iloc[0] in mean_target:
        data['state_mean']=mean_target[data['state'].iloc[0]]
    else:
        data['state_mean']=0
    
    #2
    data['rent_sale']=data['status'].apply(lambda x: 1 if str(x).lower().find('rent') >-1 else 0)
    
    #3
    data['prop_type']=data['propertyType'].apply(lambda x: replace_property(x))
    #считаем hash
    hash_space=50
    data['prop_type']=data['prop_type'].apply(lambda x: hash(''.join(str(x).lower().split())) % hash_space)
    
    #4
    # заполняем пропущенные значения на "no_city"
    data['city'].fillna('no_city', inplace=True)
    # приводим все буквы к нижнему регистру, так как есть вероятность, что города могут быть написаны по-разному
    data['city_lower'] = data['city'].apply(lambda x: str(x).lower() if x != ' ' else 'no_city')
    hash_space = 2020
    data['city_hash']=data['city'].apply(lambda x: hash(''.join(x.lower().split())) % hash_space)
    data['street_hash']=data['street'].apply(lambda x: hash(''.join(str(x).lower().split())) % hash_space)
    data['address_hash']=data[['city', 'street']].apply(lambda x: hash(''.join(str(x[0]).lower().split()) + 
                                                                  ''.join(str(x[1]).lower().split())) % hash_space, axis=1)
    
    #5
    data['baths_count']=data['baths'].apply(lambda x: make_baths_count(x))
    
    #6
    data['beds_count']=data['beds'].apply(lambda x: make_beds_count(x))
    data['beds_square']=data['beds'].apply(lambda x: make_beds_square(x))
    
    #7
    #добавляем кучу новых столбцов с характеристиками по школам
    new_columns = ['K','1','2','3','4','5','6','7','8','9','10','11','12', 'PK', 'schools_count', 
              'min_dist', 'max_dist', 'mean_dist', 'max_rate', 'average_rate_school']
    data[new_columns] = pd.DataFrame(data['schools'].apply(lambda x: make_schools(x)), index=data.index)
    
    #8
    data['sqft'].fillna(0, inplace=True)
    #убираем все символы, кроме цифр. Приводим к формату int
    regex_sq = re.compile('\D+')
    data['sqft'] = data['sqft'].apply(lambda x: regex_sq.sub('', str(x)))
    data['sqft'] = data['sqft'].apply(lambda x: int(x) if x != '' else 0)
    
    #9
    #убираем все символы, кроме цифр. Приводим к формату int
    regex = re.compile('\D+')
    data['zipcode_int'] = data['zipcode'].apply(lambda x: int(regex.sub('', str(x))) if regex.sub('', str(x))!='' else 0)
    
    #10
    data['private pool1'] = data['private pool'].apply(lambda x: 1 if str(x).lower()=='yes' else 0)
    data['PrivatePool1'] = data['PrivatePool'].apply(lambda x: 1 if str(x).lower()=='yes' else 0)
    data['pool'] = data[['PrivatePool1','private pool1']].values.max(1)
    
    #11
    data['fireplace_y_n'] = data['fireplace'].apply(lambda x: 0 if (str(x) == 'nan' 
                                                                or str(x).lower() == 'not applicable' 
                                                                or str(x).lower() == 'no') else 1)
    #посчитаем, сколько характеристик указано для дома
    data['fp_count']=data['fireplace'].apply(lambda x: len(str(x).split(',')))
    
    #12
    # заменяем нан на 1 этаж
    data['stories'].fillna(1, inplace=True)
    #убираем все символы, кроме цифр. Приводим к формату int
    regex_sq = re.compile('\D+')
    data['stories_count']=data['stories'].apply(lambda x: make_stories(x))
    
    #13
    states_list = list(states_list)
    data['state_encoding']=data['state'].apply(lambda x: states_list.index(x) if x in states_list else len(states_list))
    
    #14
    fact_columns = ['Cooling',  'Heating', 'Parking', 'Price/sqft', 'Remodeled year', 'Year built', 'lotsize']
    data[fact_columns]=data['homeFacts'].apply(lambda x: make_facts(x,fact_columns))
    #Cooling, Heating, Parking меняем на 1 (есть), 0(нет)
    for i in ['Cooling', 'Heating', 'Parking']:
        data[i].fillna(0, inplace = True)
        data[i] = data[i].apply(lambda x: 0 if x == np.nan or x in ['', 'No','None', 'no', 0, 'No Data'] else 1)
    data['price']=data['Price/sqft'].apply(lambda x: make_price(x))
    #преобразуем год в число
    for i in ['Remodeled year', 'Year built']:
        data[i.split()[0]] = data[i].apply(lambda x: int(x) if str(x) not in ['', 'None','No Data'] else 0)
    data['lot'] = data['lotsize'].apply(lambda x: make_lot(x))
    
    #15
    #соединяем идентификаторы в одну колонку, так удобнее с ними работать
    data['mls-id'].fillna('', inplace=True)
    data['MlsId'].fillna('', inplace=True)
    data['new_id']=data['mls-id'].astype(str)+data['MlsId'].astype(str)
    hash_space = 500000
    data['new_id'] = data['new_id'].apply(lambda x: hash(''.join(x.lower().split())) % hash_space)
    
    data['price_sqft'] = data['price']*data['sqft']
    data['price_lot']=data['price']*data['lot']
    
    columns = ['new_id', 'Remodeled', 'mean_dist', '9', 'schools_count', 'min_dist',
       'prop_type', '7', 'beds_square', 'Parking', 'sqft', 'zipcode_int', '6',
       '5', 'Cooling', 'beds_count', 'pool', 'lot', 'state_encoding',
       'baths_count', 'K', 'average_rate_school', 'city_hash', 'max_dist',
       'street_hash', 'price_sqft', 'stories_count', 'Year', 'PK', 'price_lot',
       '12', 'max_rate', 'address_hash', 'price', 'state_mean', '8']
    result = data[columns]
    
    return result