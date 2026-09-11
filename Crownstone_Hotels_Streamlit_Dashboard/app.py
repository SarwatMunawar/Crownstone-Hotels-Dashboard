import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
st.set_page_config(page_title="Crownstone Hotels UK Analytics",layout="wide",initial_sidebar_state="expanded")
st.markdown("""<style>
.stApp{background:#FAFBFD;color:#344054}[data-testid="stSidebar"]{background:#FFFFFF;border-right:1px solid #E7EAF0}
.kpi-card{background:#FFFFFF;border:1px solid #E7EAF0;border-radius:18px;padding:17px;box-shadow:0 4px 14px rgba(42,54,79,.05);min-height:112px}
.kpi-label{font-size:.78rem;color:#667085;font-weight:650;margin-bottom:7px}.kpi-value{font-size:1.48rem;color:#344054;font-weight:750}.kpi-note{font-size:.73rem;color:#98A2B3;margin-top:4px}
.insight-box{background:#FFFFFF;border:1px solid #ECEEF2;border-left:5px solid #CDB4DB;border-radius:12px;padding:13px 15px;margin-bottom:9px}
div[data-baseweb="select"]>div{background:#FFFFFF;border-radius:12px}.stButton>button,.stDownloadButton>button{border-radius:12px;border:1px solid #D0D5DD;background:#FFFFFF;color:#344054}
</style>""",unsafe_allow_html=True)
BASE=Path(__file__).parent
b=pd.read_csv(BASE/"Bookings_Enriched_Cleaned.csv",parse_dates=["BookingDate","CheckInDate","CheckOutDate","CancellationDate"])
hotels=pd.read_csv(BASE/"Hotels_Cleaned.csv");payments=pd.read_csv(BASE/"Payments_Cleaned.csv",parse_dates=["PaymentDate"]);reviews=pd.read_csv(BASE/"Reviews_Cleaned.csv",parse_dates=["ReviewDate"])
staff=pd.read_csv(BASE/"Staff_Cleaned.csv",parse_dates=["HireDate"]);costs=pd.read_csv(BASE/"Operating_Costs_Cleaned.csv",parse_dates=["MonthStart"])
def money(x):
    if pd.isna(x):return "£0"
    if abs(x)>=1_000_000:return f"£{x/1_000_000:.2f}M"
    if abs(x)>=1_000:return f"£{x/1_000:.1f}K"
    return f"£{x:,.0f}"
def card(label,value,note=""):st.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>',unsafe_allow_html=True)
st.title("Crownstone Hotels UK Analytics");st.caption("Commercial, operational, guest-experience and workforce intelligence")
with st.sidebar:
    st.subheader("Filters");sels={}
    for label,col in [("Hotel","HotelName"),("City","City"),("Region","Region"),("Channel Group","ChannelGroup"),("Booking Source","BookingChannel"),("Booking Status","BookingStatus"),("Loyalty Tier","LoyaltyTier"),("Room Type","RoomType")]:
        sels[col]=st.multiselect(label,sorted(b[col].dropna().unique().tolist()))
    mind,maxd=b["BookingDate"].min().date(),b["BookingDate"].max().date();dates=st.date_input("Booking Date",value=(mind,maxd),min_value=mind,max_value=maxd)
f=b.copy()
for col,vals in sels.items():
    if vals:f=f[f[col].isin(vals)]
if isinstance(dates,tuple) and len(dates)==2:f=f[(f["BookingDate"].dt.date>=dates[0])&(f["BookingDate"].dt.date<=dates[1])]
booking_ids=f["BookingID"].dropna().unique();hotel_ids=f["HotelID"].dropna().unique()
fp=payments[payments["BookingID"].isin(booking_ids)];fr=reviews[reviews["BookingID"].isin(booking_ids)];fs=staff[staff["HotelID"].isin(hotel_ids)];fc=costs[costs["HotelID"].isin(hotel_ids)]
page=st.radio("Dashboard Page",["Executive Overview","Revenue & Channels","Operations & Cost","Guest Experience","Workforce","Booking Funnel & Insights"],horizontal=True)
total=len(f);checked=(f["BookingStatus"]=="Checked Out").sum();cancelled=(f["BookingStatus"]=="Cancelled").sum();net=f["NetRevenueAfterCommissionGBP"].fillna(0).sum();val=f["BookingValueGBP"].fillna(0).sum();comm=f["ChannelCommissionGBP"].fillna(0).sum()
rn=(f.loc[f["BookingStatus"]=="Checked Out","Nights"].fillna(0)*f.loc[f["BookingStatus"]=="Checked Out","RoomsBooked"].fillna(0)).sum();adr=f.loc[f["BookingStatus"]=="Checked Out","NetRoomRevenueGBP"].fillna(0).sum()/rn if rn else 0;cancel_rate=cancelled/total*100 if total else 0
if page=="Executive Overview":
    items=[("Bookings",f"{total:,}","Filtered reservations"),("Checked Out",f"{checked:,}",f"{checked/total*100:.1f}% completed" if total else ""),("Cancellation Rate",f"{cancel_rate:.1f}%","Cancelled / bookings"),("Booking Value",money(val),"Recognised value"),("Net Revenue",money(net),"After commission"),("ADR",money(adr),"Checked-out room nights")]
    for c,v in zip(st.columns(6),items):
        with c:card(*v)
    m=f.assign(Month=f["BookingDate"].dt.to_period("M").dt.to_timestamp()).groupby("Month",as_index=False).agg(Bookings=("BookingID","count"),NetRevenue=("NetRevenueAfterCommissionGBP","sum"));c1,c2=st.columns(2)
    with c1:st.plotly_chart(px.line(m,x="Month",y="NetRevenue",markers=True,title="Monthly Net Revenue"),use_container_width=True)
    with c2:
        h=f.groupby("HotelName",as_index=False).agg(Bookings=("BookingID","count"),NetRevenue=("NetRevenueAfterCommissionGBP","sum"))
        st.plotly_chart(px.bar(h.sort_values("NetRevenue"),x="NetRevenue",y="HotelName",orientation="h",title="Net Revenue by Hotel",color="NetRevenue",color_continuous_scale="Blues"),use_container_width=True)
    c3,c4=st.columns(2)
    with c3:
        s=f["BookingStatus"].value_counts().rename_axis("Status").reset_index(name="Bookings");st.plotly_chart(px.pie(s,names="Status",values="Bookings",hole=.55,title="Booking Status Mix"),use_container_width=True)
    with c4:
        r=f.groupby("RoomType",as_index=False).agg(NetRevenue=("NetRevenueAfterCommissionGBP","sum"));st.plotly_chart(px.bar(r.sort_values("NetRevenue",ascending=False),x="RoomType",y="NetRevenue",title="Revenue by Room Type"),use_container_width=True)
elif page=="Revenue & Channels":
    direct=f.loc[f["ChannelGroup"]=="Direct","NetRevenueAfterCommissionGBP"].sum();ota=f.loc[f["ChannelGroup"]=="OTA","NetRevenueAfterCommissionGBP"].sum();disc=f["DiscountAmountGBP"].fillna(0).sum();avgv=val/total if total else 0
    items=[("Net Revenue",money(net),"After commission"),("Commission",money(comm),"Distribution cost"),("Average Booking",money(avgv),"Per reservation"),("Discounts",money(disc),"Total discount value"),("Direct Revenue",money(direct),"Direct group"),("OTA Revenue",money(ota),"OTA group")]
    for c,v in zip(st.columns(6),items):
        with c:card(*v)
    ch=f.groupby(["ChannelGroup","BookingChannel"],as_index=False).agg(Bookings=("BookingID","count"),NetRevenue=("NetRevenueAfterCommissionGBP","sum"),Commission=("ChannelCommissionGBP","sum"));c1,c2=st.columns(2)
    with c1:st.plotly_chart(px.treemap(ch,path=["ChannelGroup","BookingChannel"],values="NetRevenue",color="Commission",title="Revenue Mix and Commission"),use_container_width=True)
    with c2:
        sc=f.groupby("BookingChannel",as_index=False).agg(Bookings=("BookingID","count"),Cancelled=("BookingStatus",lambda x:(x=="Cancelled").sum()),NetRevenue=("NetRevenueAfterCommissionGBP","sum"));sc["CancellationRate"]=sc["Cancelled"]/sc["Bookings"]*100
        st.plotly_chart(px.scatter(sc,x="Bookings",y="NetRevenue",size="Bookings",color="CancellationRate",hover_name="BookingChannel",title="Source Quality"),use_container_width=True)
    rp=f.groupby("RatePlan",as_index=False).agg(NetRevenue=("NetRevenueAfterCommissionGBP","sum"),AvgNightlyRate=("NightlyRateGBP","mean"));st.plotly_chart(px.bar(rp,x="RatePlan",y="NetRevenue",color="AvgNightlyRate",title="Rate Plan Performance"),use_container_width=True)
elif page=="Operations & Cost":
    bud=fc["BudgetGBP"].fillna(0).sum();act=fc["ActualGBP"].fillna(0).sum();var=act-bud;contrib=net-act
    items=[("Operating Budget",money(bud),"Filtered hotels"),("Actual Cost",money(act),"Operating cost"),("Cost Variance",money(var),"Actual - budget"),("Net Revenue",money(net),"After commission"),("Contribution Proxy",money(contrib),"Net revenue - modelled cost"),("Contribution Margin",f"{contrib/net*100:.1f}%" if net else "0.0%","Proxy")]
    for c,v in zip(st.columns(6),items):
        with c:card(*v)
    cc=fc.groupby("CostCategory",as_index=False)[["BudgetGBP","ActualGBP"]].sum();c1,c2=st.columns(2)
    with c1:st.plotly_chart(px.bar(cc.sort_values("ActualGBP",ascending=False),x="CostCategory",y=["BudgetGBP","ActualGBP"],barmode="group",title="Budget vs Actual by Cost Category"),use_container_width=True)
    with c2:
        mt=fc.assign(Month=fc["MonthStart"].dt.to_period("M").dt.to_timestamp()).groupby("Month",as_index=False)[["BudgetGBP","ActualGBP"]].sum();st.plotly_chart(px.line(mt,x="Month",y=["BudgetGBP","ActualGBP"],markers=True,title="Monthly Cost Trend"),use_container_width=True)
    hh=fc.groupby("HotelID",as_index=False)[["BudgetGBP","ActualGBP"]].sum().merge(hotels[["HotelID","HotelName"]],on="HotelID",how="left");hh["Variance"]=hh["ActualGBP"]-hh["BudgetGBP"];st.plotly_chart(px.bar(hh.sort_values("Variance",ascending=False),x="HotelName",y="Variance",title="Cost Variance by Hotel"),use_container_width=True)
elif page=="Guest Experience":
    av=fr["OverallScore"].mean();rr=len(fr)/checked*100 if checked else 0;resp=(fr["ManagementResponseSent"].astype(str).str.lower()=="yes").mean()*100 if len(fr) else 0;dims={c:fr[c].mean() for c in ["CleanlinessScore","ServiceScore","LocationScore","ValueScore"]};best=max(dims,key=dims.get);low=min(dims,key=dims.get)
    items=[("Reviews",f"{len(fr):,}","Filtered bookings"),("Average Score",f"{av:.2f}/5" if pd.notna(av) else "N/A","Overall"),("Review Rate",f"{rr:.1f}%","Reviews / checked-out"),("Management Response",f"{resp:.1f}%","Responded reviews"),("Best Dimension",best.replace("Score",""),f"{dims[best]:.2f}/5"),("Lowest Dimension",low.replace("Score",""),f"{dims[low]:.2f}/5")]
    for c,v in zip(st.columns(6),items):
        with c:card(*v)
    rh=fr.groupby("HotelID",as_index=False).agg(OverallScore=("OverallScore","mean"),Reviews=("ReviewID","count")).merge(hotels[["HotelID","HotelName"]],on="HotelID",how="left");c1,c2=st.columns(2)
    with c1:st.plotly_chart(px.bar(rh.sort_values("OverallScore",ascending=False),x="HotelName",y="OverallScore",color="Reviews",range_y=[0,5],title="Review Score by Hotel"),use_container_width=True)
    with c2:
        src=fr.groupby("ReviewSource",as_index=False).agg(OverallScore=("OverallScore","mean"),Reviews=("ReviewID","count"));st.plotly_chart(px.scatter(src,x="Reviews",y="OverallScore",size="Reviews",hover_name="ReviewSource",range_y=[0,5],title="Review Source Profile"),use_container_width=True)
    dd=pd.DataFrame({"Dimension":[k.replace("Score","") for k in dims],"Score":list(dims.values())});st.plotly_chart(px.bar(dd,x="Dimension",y="Score",range_y=[0,5],title="Guest Experience Dimensions"),use_container_width=True)
elif page=="Workforce":
    active=(fs["EmploymentStatus"]=="Active").sum();perf=fs["PerformanceRating"].mean();training=fs["TrainingHoursYTD"].mean();absence=fs["AbsenceDaysYTD"].mean();salary=fs.loc[fs["EmploymentStatus"]=="Active","AnnualSalaryGBP"].sum()
    items=[("Staff Records",f"{len(fs):,}","Filtered hotels"),("Active Staff",f"{active:,}","Current"),("Annualised Salary",money(salary),"Active staff"),("Performance",f"{perf:.2f}/5" if pd.notna(perf) else "N/A","Average"),("Training Hours",f"{training:.1f}","Average YTD"),("Absence Days",f"{absence:.1f}","Average YTD")]
    for c,v in zip(st.columns(6),items):
        with c:card(*v)
    dep=fs.groupby("Department",as_index=False).agg(Staff=("EmployeeID","count"),Performance=("PerformanceRating","mean"),Training=("TrainingHoursYTD","mean"),Absence=("AbsenceDaysYTD","mean"));c1,c2=st.columns(2)
    with c1:st.plotly_chart(px.bar(dep.sort_values("Staff",ascending=False),x="Department",y="Staff",color="Performance",title="Workforce by Department"),use_container_width=True)
    with c2:st.plotly_chart(px.scatter(dep,x="Training",y="Performance",size="Staff",color="Absence",hover_name="Department",title="Training, Performance and Absence"),use_container_width=True)
    et=fs["EmploymentType"].value_counts().rename_axis("EmploymentType").reset_index(name="Staff");st.plotly_chart(px.pie(et,names="EmploymentType",values="Staff",hole=.55,title="Employment Type Mix"),use_container_width=True)
else:
    stages=[("Reservations",total),("Not Cancelled",total-cancelled),("Checked Out",checked),("Reviewed",len(fr))];repeat=f["GuestID"].value_counts();repeat_rate=(repeat.gt(1).sum()/repeat.size*100) if repeat.size else 0
    items=[("Reservations",f"{total:,}","Filtered"),("Not Cancelled",f"{total-cancelled:,}",f"{(total-cancelled)/total*100:.1f}% retained" if total else ""),("Checked Out",f"{checked:,}",f"{checked/total*100:.1f}% completed" if total else ""),("Reviews",f"{len(fr):,}",f"{len(fr)/checked*100:.1f}% review rate" if checked else ""),("Repeat Guest Rate",f"{repeat_rate:.1f}%","Guests with >1 booking")]
    for c,v in zip(st.columns(5),items):
        with c:card(*v)
    ff=pd.DataFrame(stages,columns=["Stage","Count"]);fig=go.Figure(go.Funnel(y=ff["Stage"],x=ff["Count"],textinfo="value+percent initial"));fig.update_layout(title="Booking Lifecycle Funnel");st.plotly_chart(fig,use_container_width=True)
    if total:
        sc=f.groupby("BookingChannel",as_index=False).agg(Bookings=("BookingID","count"),Cancelled=("BookingStatus",lambda x:(x=="Cancelled").sum()),NetRevenue=("NetRevenueAfterCommissionGBP","sum"));sc["CancellationRate"]=sc["Cancelled"]/sc["Bookings"]*100;best=sc.sort_values("NetRevenue",ascending=False).iloc[0];high=sc.sort_values("CancellationRate",ascending=False).iloc[0];hp=f.groupby("HotelName",as_index=False).agg(NetRevenue=("NetRevenueAfterCommissionGBP","sum")).sort_values("NetRevenue",ascending=False).iloc[0]
        for text in [f"{hp['HotelName']} is the highest filtered revenue property at {money(hp['NetRevenue'])}.",f"{best['BookingChannel']} leads booking sources by net revenue at {money(best['NetRevenue'])}.",f"{high['BookingChannel']} has the highest filtered cancellation rate at {high['CancellationRate']:.1f}%.",f"Filtered channel commission is {money(comm)} and directly reduces booking contribution.",f"The filtered cancellation rate is {cancel_rate:.1f}%; reducing it protects late-stage demand and revenue."]:st.markdown(f'<div class="insight-box">{text}</div>',unsafe_allow_html=True)
    st.subheader("Recommendations")
    for t,r in [("Increase profitable direct demand","Use loyalty, member-only offers and remarketing to reduce commission leakage."),("Reduce high-cancellation source exposure","Review rate rules, deposits and cancellation windows by source."),("Improve the weakest guest-rating dimension","Target hotel-level service actions where ratings are lowest."),("Control recurring cost overruns","Assign category owners and monthly variance thresholds."),("Manage hotels on contribution, not revenue alone","Compare net revenue after commission with operating cost."),("Link workforce measures to service outcomes","Use training, absence and performance alongside review scores.")]:st.markdown(f'<div class="insight-box"><b>{t}</b><br>{r}</div>',unsafe_allow_html=True)
st.divider();st.caption(f"Filtered booking rows: {len(f):,}. KPI cards and charts recalculate from the active filters.")
