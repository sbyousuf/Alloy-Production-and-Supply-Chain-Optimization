from pyomo.environ import *

# مدل
model = ConcreteModel()
M = 1e6  
#  مجموعه‌ها
model.alloys = Set(initialize=['A', 'B'])  # انواع آلیاژ
model.production_facilities = Set(initialize=['0', '1', '2'])  # کارخانه‌های تولید
model.metals = Set(initialize=['Fe', 'Cu', 'Zn', 'Al'])  # انواع فلز
model.ore_types = Set(initialize=['1', '2', '3'])  # انواع سنگ معدن
model.storage_facilities = Set(initialize=['E', 'T'])  # انبارها
model.cities = Set(initialize=['M', 'Z', 'K', 'TA'])  # شهرها

# متغیرها
model.O = Var(model.ore_types, domain=NonNegativeReals)  # مقدار سنگ معدن استخراج‌شده
model.MP = Var(model.metals, model.alloys, domain=NonNegativeReals)  # درصد فلزها در آلیاژ
model.AP = Var(model.alloys, model.production_facilities, domain=NonNegativeReals)  # مقدار تولید آلیاژ
model.AB = Var(model.alloys, model.production_facilities, domain=NonNegativeReals)  # مقدار خرید آلیاژ
model.ATS = Var(model.alloys, model.production_facilities, model.storage_facilities, domain=NonNegativeReals)  # انتقال به انبار
model.AIC = Var(model.alloys, model.storage_facilities, model.cities, domain=NonNegativeReals)
model.CCC = Var(model.storage_facilities, model.cities, within=Integers)  # Container transport (storage -> city)
model.CCS = Var(model.production_facilities, model.storage_facilities, within=Integers)  # Container transport (factory -> storage)
model.ES = Var(model.production_facilities, model.storage_facilities, within=Binary)  # Extra storage (factory -> storage)
model.EC = Var(model.storage_facilities, model.cities, within=Binary)  # Extra containers (storage -> city)
model.C = Var(model.production_facilities,  within=Binary)  # Some integer variable related to production
model.r = Var(model.production_facilities, model.storage_facilities, within=NonNegativeReals, bounds=(0, 99))
model.R = Var(model.storage_facilities,  model.cities, within=NonNegativeReals, bounds=(0, 99))


# محدودیت ها 
#----------------------------------------------------------------------------------------------------
metal_content = {
    '1': {'Zn': 0.25, 'Fe': 0.05, 'Cu': 0.3, 'Al': 0.35,'Other': 0.5},  
    '2': {'Zn': 0.15, 'Fe': 0.2, 'Cu': 0.25, 'Al': 0.3,'Other': 0.1},
    '3': {'Zn': 0.05, 'Fe': 0.05, 'Cu': 0.65, 'Al': 0.25,'Other': 0}
}
def zinc_constraint_rule(model):
    return (model.O['1'] * 0.25 + model.O['2'] * 0.15 + model.O['3'] * 0.05
            >= model.MP['Zn', 'A'] + model.MP['Zn', 'B'])

model.ZincConstraint = Constraint(rule=zinc_constraint_rule)

def iron_constraint_rule(model):
    return (model.O['1'] * 0.05 + model.O['2'] * 0.2 + model.O['3'] * 0.05
            >= model.MP['Fe', 'A'] + model.MP['Fe', 'B'])

model.IronConstraint = Constraint(rule=iron_constraint_rule)

def copper_constraint_rule(model):
    return (model.O['1'] * 0.3 + model.O['2'] * 0.25 + model.O['3'] * 0.65
            >= model.MP['Cu', 'B'] + model.MP['Cu', 'A'])

model.CopperConstraint = Constraint(rule=copper_constraint_rule)

def aluminum_constraint_rule(model):
    return (model.O['1'] * 0.35 + model.O['2'] * 0.3 + model.O['3'] * 0.25
            >= model.MP['Al', 'A']  + model.MP['Al', 'B'])

model.AluminumConstraint = Constraint(rule=aluminum_constraint_rule)
#------------------------------------------------------------------------------------------------------
# حداکثر مقدار سنگ معدن در دسترس
maxOre = {'1': 560, '2': 1000, '3': 1440}
model.max_ore_1 = Constraint(expr=model.O['1'] <= maxOre['1'])
model.max_ore_2 = Constraint(expr=model.O['2'] <= maxOre['2'])
model.max_ore_3 = Constraint(expr=model.O['3'] <= maxOre['3'])
#------------------------------------------------------------------------------------------------------
model.max_ore_df3 = Constraint(expr=model.AP['B','0'] <= model.MP['Cu', 'B'] + model.MP['Al', 'B']+ model.MP['Zn', 'B']+model.MP['Fe','B'])
model.max_ore_df4 = Constraint(expr=model.AP['A','0']<=model.MP['Zn', 'A'] +model.MP['Fe', 'A'] + model.MP['Cu', 'A'] +  model.MP['Al', 'A'])
#------------------------------------------------------------------------------------------------------
#جدول 1 
Percentage = {
    ('A', 'Zn'): 0.80,   # Alloy A: Max 80% Zinc
    ('A', 'Fe'): 0.25,   # Alloy A: Max 25% Iron
    ('A', 'Al'): 0.55,   # Alloy A: Min 55% Aluminum
    ('B', 'Fe'): (0.45, 0.70),  # Alloy B: Between 45% and 70% Iron
    ('B', 'Cu'): 0.35,   # Alloy B: Min 35% Copper
    ('B', 'Al'): 0.70    # Alloy B: Max 70% Aluminum
}
model.MetalBalanceConstraint_zn = Constraint(
    expr=model.MP['Zn', 'A'] * 0.2 <= 
         0.8 * model.MP['Fe', 'A'] + 0.8 * model.MP['Cu', 'A'] + 0.8 * model.MP['Al', 'A']
)
model.MetalBalanceConstraint_Fe1 = Constraint(
    expr=0.75 * model.MP['Fe', 'A']  <= 
          0.25 * model.MP['Cu', 'A'] + 0.25 * model.MP['Al', 'A']+model.MP['Zn', 'A']*0.25
)
model.MetalBalanceConstraint_Fe2 = Constraint(
    expr=0.3 * model.MP['Fe', 'B']  <= 
          0.7 * model.MP['Cu', 'B'] + 0.7 * model.MP['Al', 'B']+model.MP['Zn', 'B']*0.7
)
model.MetalBalanceConstraint_Fe3 = Constraint(
    expr=0.55 * model.MP['Fe', 'B'] >= 
          0.45 * model.MP['Cu', 'B'] + 0.45 * model.MP['Al', 'B']+model.MP['Zn', 'B']*0.45
)
model.MetalBalanceConstraint_Cu = Constraint(
    expr=0.65 * model.MP['Cu', 'B']  >= 
          0.35 * model.MP['Al', 'B'] + 0.35 * model.MP['Fe', 'B']+model.MP['Zn', 'B']*0.35
)
model.MetalBalanceConstraint_AL1 = Constraint(
    expr=0.45 * model.MP['Al', 'A']  <= 
          0.55 * model.MP['Cu', 'A'] + 0.55 * model.MP['Fe', 'A']+model.MP['Zn', 'A']*0.55
)
model.MetalBalanceConstraint_Al2 = Constraint(
    expr=0.3 * model.MP['Al', 'B']  <= 
          0.7 * model.MP['Fe', 'B'] + 0.7 * model.MP['Cu', 'B']+model.MP['Zn', 'B']*0.35
)
#-----------------------------------------------------------------------------------------------
# ربط دادن مقدار آلیاژ ساخته شده یا خریده شده به مقدار آلیاژی که وارد انبار ها میشود 
model.alloy_to_storage_A0 = Constraint(expr=(model.AP['A', '0'] + model.AB['A', '0']) >= model.ATS['A', '0', 'T'] + model.ATS['A', '0', 'E'])
model.alloy_to_storage_B0 = Constraint(expr=(model.AP['B', '0'] + model.AB['B', '0']) >= model.ATS['B', '0', 'T'] + model.ATS['B', '0', 'E'])

model.alloy_to_storage_A1 = Constraint(expr=(model.AP['A', '1'] + model.AB['A', '1']) >= model.ATS['A', '1', 'T'] + model.ATS['A', '1', 'E'])
model.alloy_to_storage_B1 = Constraint(expr=(model.AP['B', '1'] + model.AB['B', '1']) >= model.ATS['B', '1', 'T'] + model.ATS['B', '1', 'E'])

model.alloy_to_storage_A2 = Constraint(expr=(model.AP['A', '2'] + model.AB['A', '2']) >= model.ATS['A', '2', 'T'] + model.ATS['A', '2', 'E'])
model.alloy_to_storage_B2 = Constraint(expr=(model.AP['B', '2'] + model.AB['B', '2']) >= model.ATS['B', '2', 'T'] + model.ATS['B', '2', 'E'])

#-----------------------------------------------------------------------------------------------
#محدو دیت حمل و نقل به انبار ها
container_limits_fs = {
    ('0', 'T'): (5, 20), ('0', 'E'): (5, 20),
    ('1', 'T'): (10, 30), ('1', 'E'): (10, 30),
    ('2', 'T'): (5, 25), ('2', 'E'): (5, 15)
}
model.container_constraints = ConstraintList()
for f, s in container_limits_fs.keys():
    min_limit, max_limit = container_limits_fs[(f, s)]
    model.container_constraints.add(expr=model.CCS[f, s] + model.ES[f, s] >= min_limit)  # Minimum transport limit
    model.container_constraints.add(expr=model.CCS[f, s] + model.ES[f, s] <= max_limit)  # Maximum transport limit
#------------------------------------------------------------------------------------------------
# محدودیت محموع حمل و نقل به انبارها 
transport_limits = {
    'T': {'min': 20, 'max': 65},  # Tehran
    'E': {'min': 30, 'max': 70}   # Isfahan
}
model.transport_constraints = ConstraintList()
model.transport_constraints.add(
    sum(model.CCS[f, 'T'] + model.ES[f, 'T'] for f in model.production_facilities) <= transport_limits['T']['max']
)
model.transport_constraints.add(
    sum(model.CCS[f, 'T'] + model.ES[f, 'T'] for f in model.production_facilities) >= transport_limits['T']['min']
)

# Constraints for Isfahan (E)
model.transport_constraints.add(
    sum(model.CCS[f, 'E'] + model.ES[f, 'E'] for f in model.production_facilities) <= transport_limits['E']['max']
)
model.transport_constraints.add(
    sum(model.CCS[f, 'E'] + model.ES[f, 'E'] for f in model.production_facilities) >= transport_limits['E']['min']
)
#---------------------------------------------------------------------------------------------------
# محدودیت حمل و نقل به شهر ها
# جدول 6
container_limits_sc = {
    ('T', 'M'): (3, 7), ('T', 'K'): (6, 12), ('T', 'Z'): (10, 18), ('T', 'TA'): (5, 15),
    ('E', 'M'): (4, 6), ('E', 'K'): (5, 14), ('E', 'Z'): (5, 20), ('E', 'TA'): (10, 20)
}
model.city_transport_limits = ConstraintList()
for (storage, city), (min_limit, max_limit) in container_limits_sc.items():
    model.city_transport_limits.add(model.CCC[storage, city] + model.EC[storage, city] <= max_limit)
    model.city_transport_limits.add(model.CCC[storage, city] + model.EC[storage, city] >= min_limit)
#----------------------------------------------------------------------------------------------------
#: محدودیت تقاضا در شهر های مختلف
demand = {('M', 'A'): 600, ('K', 'A'): 800, ('Z', 'A'): 1500, ('TA', 'A'): 1400, ('M', 'B'): 400, ('K', 'B'): 1200, ('Z', 'B'): 1500, ('TA', 'B'): 1100}
model.demand_constraints = ConstraintList()
for (city, alloy), max_demand in demand.items():
    model.demand_constraints.add(
        expr=sum(model.AIC[alloy,storage, city ] for storage in model.storage_facilities) <= max_demand)
#----------------------------------------------------------------------------------------------------
# :سفارش از کارخانه هاي ثانويه
#حداقل سفارش برحسب تن
minOrder = {'0':0,'1': 2000, '2': 2500}  # Minimum total alloy order per factory
#حداکثر سفارش برحسب تن
maxOrder = {'0':0,'1': 5000, '2': 6000}  # Maximum total alloy order per factory
model.contract_constraints = ConstraintList()
for f in model.production_facilities:
    model.contract_constraints.add(sum(model.AB[i, f] for i in model.alloys) >= minOrder[f] * model.C[f])
    model.contract_constraints.add(sum(model.AB[i, f] for i in model.alloys) <= maxOrder[f] * model.C[f])
#-------------------------------------------------------------------------------------------------------  
def transfer_equation1_rule(model, f, s):
    return (
        sum(model.ATS[i,f, s] for i in model.alloys)<= model.CCS[f,s] * 100 )
model.TransferEquation1 = Constraint(model.production_facilities,model.storage_facilities, rule=transfer_equation1_rule)

def transfer_equation2_rule(model, S, C):
    return (
        sum(model.AIC[i,S, C] for i in model.alloys)<= model.CCC[S,C] * 100 )
model.TransferEquation2 = Constraint(model.storage_facilities, model.cities, rule=transfer_equation2_rule)
#--------------------------------------------------------------------------------
model.StorageToCity_Constraint1 = ConstraintList()
for s in model.storage_facilities:
    for c in model.cities:
        model.StorageToCity_Constraint1.add(
            sum(model.AIC[i, s, c] for i in model.alloys) == 100 * model.CCC[s, c] + model.R[s, c]
        )

model.StorageToCity_Constraint2 = Constraint(model.storage_facilities, model.cities, rule=lambda model, s, c:
    model.R[s, c] <= 100
)

model.StorageToCity_Constraint3 = Constraint(model.storage_facilities, model.cities, rule=lambda model, s, c:
    model.R[s, c] / 100 <= M * model.EC[s, c]
)

#
model.balance_constraint = Constraint(
    model.alloys, model.storage_facilities,
    rule=lambda model, i, S: 
        sum(model.ATS[i, F, S] for F in model.production_facilities) >= 
        sum(model.AIC[i, S, C] for C in model.cities)
)
#--------------------------------------------------------------------------------
# Constraints to force specific alloy production and purchases to be zero
model.zero_production = ConstraintList()
model.zero_production.add(model.AP['A', '1'] == 0)
model.zero_production.add(model.AP['B', '1'] == 0)
model.zero_production.add(model.AP['A', '2'] == 0)
model.zero_production.add(model.AP['B', '2'] == 0)

model.zero_purchase = ConstraintList()
model.zero_purchase.add(model.AB['A', '0'] == 0)
model.zero_purchase.add(model.AB['B', '0'] == 0)
model.zero_MP_CuA = Constraint(expr=model.MP['Cu', 'A'] == 0)
model.zero_MP_ZnB = Constraint(expr=model.MP['Zn', 'B'] == 0)
model.zero_C_0 = Constraint(expr=model.C['0'] == 0) 
#==============================================================================
 ### تابع هدف
#جدول 4
TCS = {
    ('0', 'T'): 200, ('0', 'E'): 230,
    ('1', 'T'): 180, ('1', 'E'): 210,
    ('2', 'T'): 240, ('2', 'E'): 220
}

# جدول 5
TCC = {
    ('T', 'M'): 110, ('T', 'K'): 85, ('T', 'Z'): 120, ('T', 'TA'): 100,
    ('E', 'M'): 100, ('E', 'K'): 100, ('E', 'Z'): 110, ('E', 'TA'): 90
}
costProd = {('0', 'A'): 250, ('0', 'B'): 250, ('1', 'A'): 0, ('1', 'B'): 0, ('2', 'A'): 0, ('2', 'B'): 0}
# هزینه استخراج هر سنگ معدن
costOre = {'1': 45, '2': 65, '3': 70}
#هزینه اولیه قرارداد
costContract = {'0': 0, '1': 120, '2': 90}
#قیمت هر تن آلیاژ
costBuy = {('0', 'A'): 0, ('0', 'B'): 0, ('1', 'A'): 375, ('1', 'B'): 520, ('2', 'A'): 390, ('2', 'B'): 540}
initial_cost = 250
model.cost_change = Param(initialize=initial_cost, mutable=True)
model.deal1=Param(initialize=(costContract['1']), mutable=True)
model.deal2=Param(initialize=(costContract['2']), mutable=True)

# هزینه‌ها
def cost_rule(model):
    return model.Total_Cost_expr == (
        45 * model.O['1'] + 65 * model.O['2'] + 70 * model.O['3'] +
       model.cost_change* (model.AP['A','0'] + model.AP['B','0']) +
        costBuy['1','A'] * model.AB['A','1'] + costBuy['B','1'] * model.AB['B','1'] +
        costBuy['2','A']* model.AB['A','2'] + costBuy['2','B'] * model.AB['B','2'] +
        model.deal1 * model.C['1'] + model.deal2 * model.C['2'] +
        sum(sum((model.CCS[F, S] ) * TCS[F, S]
                for S in model.storage_facilities) for F in model.production_facilities) +
        sum(sum((model.CCC[S, C] ) * TCC[S, C]
                for C in model.cities) for S in model.storage_facilities)
    )
model.Total_Cost_expr = Var(domain=NonNegativeReals, initialize=0)
model.Total_Cost = Constraint(rule=cost_rule)
#-------------------------------------------------------------------------------
#جدول 7
 # قیمت فروش به هریک از کارخانهها
ASP = {('A', 'M'): 520, ('A', 'K'): 540, ('A', 'Z'): 490, ('A', 'TA'): 500, ('B', 'M'): 700, ('B', 'K'): 690, ('B', 'Z'): 730, ('B', 'TA'): 710}
# درآمدها
def revenue_rule(model):
    return model.Total_Revenue_expr == sum(
        model.AIC[i, S, C] * ASP[i, C]
        for i in model.alloys
        for S in model.storage_facilities
        for C in model.cities
    )
model.Total_Revenue_expr = Var(domain=NonNegativeReals)
model.Total_Revenue = Constraint(rule=revenue_rule)
#-------------------------------------------------------------------------------
# تابع هدف: بیشینه‌سازی سود (درآمد - هزینه)
def objective_rule(model):
    return model.Total_Revenue_expr - model.Total_Cost_expr

model.Profit = Objective(rule=objective_rule, sense=maximize)
#===============================================================================
# Solve with Gurobi
solver = SolverFactory("glpk")
result = solver.solve(model, tee=True) 

with open("D:بخش الف.txt", "w") as f:
    model.display(ostream=f)
    
    
#==============================================================================
# حلقه تحلیل حساسیت بخش د
while True:
    # حل مدل
    results = solver.solve(model)
    if model.AP['A','0'].value+model.AP['B','0'].value==0:
        threshold_cost = model.cost_change.value
        break

    # افزایش cost به مقدار step (10 واحد)
    model.cost_change.set_value(model.cost_change.value + 10)

# خروجی
print(f"هزینه بحرانی : {threshold_cost}")  
model.cost_change=250

#==============================================================================
# حلقه تحلیل حساسیت بخش ه
# قرارداد 1 
while True:
    # حل مدل
    results = solver.solve(model)
    if model.AB['A','1'].value+model.AB['B','1'].value==0:
        threshold_cost = model.deal1.value
        break

  
  # افزایش cost به مقدار step (10 واحد)
    model.deal1.set_value(model.deal1.value +10000)
    print(model.deal1.value)

# خروجی
print(f"هزینه بحرانی : {threshold_cost}")  
model.deal1=120
#----------------------------------------------------------------
# قرارداد 2
while True:
    # حل مدل
    results = solver.solve(model)
    if model.AB['A','2'].value+model.AB['B','2'].value==0:
        threshold_cost = model.deal2.value
        break

  
  # افزایش cost به مقدار step (10 واحد)
    model.deal2.set_value(model.deal2.value +10000)
    print(model.deal2.value)

# خروجی
print(f"هزینه بحرانی : {threshold_cost}")  
model.deal1=90
#===============================================================================
# بخش و
def sensitivity_analysis_with_cost(model, cost_dict, cost_key, cost_range):
    initial_basis, initial_obj = None, None

    for cost in cost_range:
        # به‌روزرسانی پارامتر هزینه
        model.cost[cost_key] = cost
        
        # حل مدل
        results = solver.solve(model)
        
        # بررسی پایه و مقدار تابع هدف
        active_vars = {var.name: var.value for var in model.component_objects(Var, active=True) if var.value > 1e-6}
        current_obj = model.obj()

        # نمایش نتایج
        print(f"Cost = {cost} -> Objective = {current_obj}, Active Variables = {active_vars}")

        if initial_basis is None:
            initial_basis = active_vars
            initial_obj = current_obj
        elif active_vars != initial_basis:
            print(f"Optimal basis changed at cost = {cost}")
            break

