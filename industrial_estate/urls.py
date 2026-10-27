
from django.urls import path
from . import views
from .views import (
    UnitPlotAllocationListView,
    UnitPlotAllocationCreateView,
    UnitPlotAllocationUpdateView,
)
from .views import FloorSpaceRentalCreateView
app_name = "industrial_estate"

urlpatterns = [
    # Industrial estates
    path("", views.estate_list, name="estate_list"),
    path("add/", views.EstateCreateView.as_view(), name="estate_create"),
    path("<int:pk>/", views.estate_detail, name="estate_detail"),
    path("<int:pk>/edit/", views.EstateUpdateView.as_view(), name="estate_update"),
    path("<int:pk>/layout-revisions/add/", views.layout_revision_add, name="layout_revision_add"),

    # Location APIs
    path("api/location-options/", views.location_options, name="location_options"),
    path("api/districts/", views.districts_by_division, name="districts_by_division"),
    path("api/upazilas/", views.upazilas_by_district, name="upazilas_by_district"),

    # Plots
    path("plots/", views.plot_list_all, name="plot_list_all"),
    path("<int:estate_pk>/plots/", views.plot_list, name="plot_list"),
    path("plots/add/", views.PlotCreateView.as_view(), name="plot_create"),
    path("plots/<int:pk>/edit/", views.PlotUpdateView.as_view(), name="plot_update"),

    # Industrial units
    path("units/", views.IndustrialUnitListView.as_view(), name="industrial_unit_list"),
    path("units/add/", views.IndustrialUnitCreateView.as_view(), name="industrial_unit_create"),
    path("units/<int:pk>/", views.IndustrialUnitDetailView.as_view(), name="industrial_unit_detail"),
    path("units/<int:pk>/edit/", views.IndustrialUnitUpdateView.as_view(), name="industrial_unit_update"),
    path("estate_reviews/", views.estate_review_queue, name="estate_review_queue"),
    path("estate_reviews/<int:pk>/action/", views.estate_review_action,name="estate_review_action",),
    # Plot allocations
    path("plot_allocations/", UnitPlotAllocationListView.as_view(), name="allocation_list"),
    path("plot_allocations/add/", UnitPlotAllocationCreateView.as_view(), name="allocation_create"),
    path("plot_allocations/<int:pk>/edit/", UnitPlotAllocationUpdateView.as_view(), name="allocation_update"),

    # Products
    path("products/", views.ProductListView.as_view(), name="product_list"),
    path("products/add/", views.ProductCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/edit/", views.ProductUpdateView.as_view(), name="product_update"),

    


    # Monthly receivables and payments
    path("receivables/", views.ReceivableListView.as_view(), name="receivable_list"),
    path("receivables/add/", views.ReceivableCreateView.as_view(), name="receivable_create"),
    path("receivables/<int:pk>/edit/", views.ReceivableUpdateView.as_view(), name="receivable_update"),
    path("payments/add/", views.PaymentCreateView.as_view(), name="payment_create"),
    path("payments/<int:pk>/edit/", views.PaymentUpdateView.as_view(), name="payment_update"),

    # Bank loans and documents
    path("bank-loans/", views.BankLoanListView.as_view(), name="bank_loan_list"),
    path("bank-loans/add/", views.BankLoanCreateView.as_view(), name="bank_loan_create"),
    path("bank-loans/<int:pk>/edit/", views.BankLoanUpdateView.as_view(), name="bank_loan_update"),
    path("bank-loan-documents/add/", views.BankLoanDocumentCreateView.as_view(), name="bank_loan_document_create"),

    # Transfers
    path("transfers/", views.TransferListView.as_view(), name="transfer_list"),
    path("transfers/add/", views.TransferCreateView.as_view(), name="transfer_create"),
    path("transfers/<int:pk>/edit/", views.TransferUpdateView.as_view(), name="transfer_update"),

    # Plot cancellation and appeals
    path("appeals/add/", views.AppealCreateView.as_view(), name="appeal_create"),
    path("appeals/<int:pk>/edit/", views.AppealUpdateView.as_view(), name="appeal_update"),

    # Export products
    path("export-products/", views.ExportProductListView.as_view(), name="export_product_list"),
    path("export-products/add/", views.ExportProductCreateView.as_view(), name="export_product_create"),
    path("export-products/<int:pk>/edit/", views.ExportProductUpdateView.as_view(), name="export_product_update"),

    # Environmental data and utility usage
    path("environment/add/", views.EnvironmentalDataCreateView.as_view(), name="environment_create"),
    path("environment/<int:pk>/edit/", views.EnvironmentalDataUpdateView.as_view(), name="environment_update"),
    path("utility-usage/add/", views.UtilityUsageCreateView.as_view(), name="utility_usage_create"),
    path("utility-usage/<int:pk>/edit/", views.UtilityUsageUpdateView.as_view(), name="utility_usage_update"),
    path(
        "unit-production/",
        views.unit_production_list,
        name="unit_production_list",
    ),
    path(
        "unit-production/<int:pk>/",
        views.unit_production_update,
        name="unit_production_update",
    ),
    path(
        "unit-production/<int:pk>/products/<int:product_pk>/delete/",
        views.unit_product_delete,
        name="unit_product_delete",
    ),
    path(
        "plot_allocations/<int:pk>/delete/",
        views.unit_plot_allocation_delete,
        name="allocation_delete",
    ),
    # Employment history
    path(
        "employment/",
        views.employment_list,
        name="employment_list",
    ),
    path(
        "units/<int:pk>/status/",
        views.unit_status_update,
        name="unit_status_update",
    ),
    path(
        "units/<int:unit_pk>/employment/add/",
        views.employment_create,
        name="employment_create",
    ),
    path(
        "units/<int:unit_pk>/employment/<int:pk>/edit/",
        views.employment_update,
        name="employment_update",
    ),
    path(
        "units/<int:unit_pk>/employment/<int:pk>/delete/",
        views.employment_delete,
        name="employment_delete",
    ),
# Floor space rental information
    path(
        "industrial-units/<int:unit_id>/floor-rental/add/",
        FloorSpaceRentalCreateView.as_view(),
        name="floor_rental_create",
    ),
    #Legal Case Url
    path(
        "legal-cases/add/",
        views.LegalCaseCreateView.as_view(),
        name="legal_case_create",
    ),
    #Greenery Report Url
    path(
        "greenery/settings/",
        views.greenery_setting_view,
        name="greenery_setting",
    ),
    path(
        "greenery/<int:estate_pk>/add/",
        views.greenery_report_create,
        name="greenery_report_create",
    ),
    # Page 6: KPI institution
    path(
        "kpi_institutions/<int:estate_pk>/add/",
        views.KPIInstitutionCreateView.as_view(),
        name="kpi_institution_create",
    ),
    path(
        "kpi_institutions/<int:estate_pk>/report/",
        views.KPIInstitutionReportView.as_view(),
        name="kpi_institution_report",
    ),
   
    # Page 7: Street lights
    path(
        "street_lights/<int:estate_pk>/add/",
        views.StreetLightCreateView.as_view(),
        name="street_light_create",
    ),
    path(
        "street_lights/<int:estate_pk>/report/",
        views.StreetLightReportView.as_view(),
        name="street_light_report",
    ),

    # Page 8.1: Water
    path(
        "water_supply/<int:estate_pk>/add/",
        views.WaterSupplyCreateView.as_view(),
        name="water_supply_create",
    ),
    path(
        "water_supply/<int:estate_pk>/report/",
        views.WaterSupplyReportView.as_view(),
        name="water_supply_report",
    ),

    # Page 8.2: Electricity
    path(
        "electricity/<int:estate_pk>/add/",
        views.ElectricityCreateView.as_view(),
        name="electricity_create",
    ),
    path(
        "electricity/<int:estate_pk>/report/",
        views.ElectricityReportView.as_view(),
        name="electricity_report",
    ),

    # Page 8.3: Gas
    path(
        "gas_supply/<int:estate_pk>/add/",
        views.GasSupplyCreateView.as_view(),
        name="gas_supply_create",
    ),
    path(
        "gas_supply/<int:estate_pk>/report/",
        views.GasSupplyReportView.as_view(),
        name="gas_supply_report",
    ),

    # Page 9: Ponds
    path(
        "ponds/<int:estate_pk>/add/",
        views.PondRecordCreateView.as_view(),
        name="pond_create",
    ),
    path(
        "ponds/<int:estate_pk>/report/",
        views.PondRecordReportView.as_view(),
        name="pond_report",
    ),

    # Page 10: Estate purpose
    path(
        "estate_purpose/<int:estate_pk>/add/",
        views.EstatePurposeCreateView.as_view(),
        name="estate_purpose_create",
    ),
    path(
        "estate_purpose/<int:estate_pk>/report/",
        views.EstatePurposeReportView.as_view(),
        name="estate_purpose_report",
    ),
]
