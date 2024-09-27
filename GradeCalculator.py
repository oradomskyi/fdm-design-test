class GradeCalculator:
    '''Class for calculating the tons of metal grades
    necessay to produce required monthly amount of particular quality group
    based on average prportion over several previous months'''

    def __init__(self, db):
        self.db = db

    def getGradesEstimate(self, month, year, tons_per_hit=100, history_window=3):
        '''Calculate the grades for based on forecast amont and production over previous months'''
        # get the production history
        # it is possible to move this logic to SQL side
        # this logic is far from ideal
        # but it works

        # retrieve order forecast from database
        production_required = self.db.get_order_forecast_1_month(year, month)
        
        # retrieve available quality groups
        quality_groups = self.db.get_rows(self.db.db_table_quality_groups)
        
        # make a dictionary of {group_id : group_name}
        group_names = {}
        for qg in quality_groups:
            qg_id = qg[0]
            qg_name = qg[1]
            group_names[qg_id] = qg_name

        #retrieve grades
        grades = self.db.get_rows(self.db.db_table_grades)
        
        # create dicts {grade_id : grade_group} and {grade_id : grade_name}
        grade_group = {}
        grade_names = {}
        for g in grades:
            grade_group[g[0]] = g[1]
            grade_names[g[0]] = g[2]

        #  a dictionary with grade fractions over several months
        # { group : { grade : [ fraction_month_1, fraction_month_2, ... ] }, }
        group_grade_fractions = {}
        # august july lune
        for i in range(history_window):
            # retrieve production for a particular year and month
            production_history = self.db.get_production_history_1_month(year, month - i - 1)

            # total tons produced of a specific group in a given month
            group_total_tons = {}
            for grade_production in production_history:
                # [ ID Month Year GradeID Tons ]
                grade_id = grade_production[3]
                tons = grade_production[4]
                
                # accumulate tons of each grade into a corresponding group
                group_id = grade_group[grade_id]
                if group_id not in group_total_tons:
                    group_total_tons[group_id] = tons
                else:
                    group_total_tons[group_id] += tons

            # fraction of total for each grade 
            # x = tons_grade_i / tons_group_total
            grade_fraction = {}
            for grade_production in production_history:
                grade_id = grade_production[3]
                tons = grade_production[4]
                group_id = grade_group[grade_id]

                grade_fraction[grade_id] = tons / group_total_tons[group_id]

                if group_id not in group_grade_fractions:
                    group_grade_fractions[group_id] = {}

                if grade_id not in group_grade_fractions[group_id]:
                    group_grade_fractions[group_id][grade_id] = []

                group_grade_fractions[group_id][grade_id].append(grade_fraction[grade_id])

        # calculate grade average fraction over few month
        # (grade_fraction_month1 + grade_fraction_month2 + ...  + grade_fraction_monthN) / N
        group_grade_averages = {}
        for group_id, grade_fractions in group_grade_fractions.items():
            group_grade_averages[group_id] = {}
            for grade_id, fractions in grade_fractions.items():
                group_grade_averages[group_id][grade_id] = sum(fractions) / len(fractions)
        
        # given the required number of heats, compute tons of each grade based on average
        # over N months
        estimated_grade_tons = {}
        for group_heats in production_required:
            # [ ID Year Month QualityGroupID Heats ]
            group_id = group_heats[3]
            heats = group_heats[4]

            group_name = group_names[group_id]
            estimated_grade_tons[group_name] = {}
            for grade_id, average in group_grade_averages[group_id].items():
                grade_name = grade_names[grade_id]
                estimated_grade_tons[group_name][grade_name] = round((heats * tons_per_hit) * average)

        return estimated_grade_tons