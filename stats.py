from datetime import timedelta

def build_stats(entries, today, days = 7):
    if entries == []:
        return {"saved":0, "wasted":0, "money_saved":0.0, "by_day": []}
    savedEntries = 0
    wastedEntries = 0
    money = 0.0
    for entry in entries:
        if entry["status"] == "saved":
            savedEntries+=1
            money+=entry.get("price",0)
        elif entry["status"] == "wasted":
            wastedEntries+=1
    return {"saved": savedEntries, "wasted": wastedEntries, "money_saved": round(money,2), "by_day": daily_breakdown(entries, today, days)}
        
        
        
def daily_breakdown(entries, today, days=7):
    counts = {}
    day_texts = []
    for day in range(days - 1,-1,-1):
        date_num = today - timedelta(days = day)
        date_text = date_num.isoformat()
        day_texts.append(date_text)
        counts[date_text] = {"saved":0, "wasted":0}
    for entry in entries:
        day = entry["date"]                
        status = entry["status"]            
        if day in counts:                  
            day_counts = counts[day]      
            day_counts[status] += 1  
    result = []
    for text in day_texts:
        result.append({"date":text, "saved": counts[text]["saved"], "wasted": counts[text]["wasted"]})
        
    return result
            
        
        
        
    
        
        
            
    
        