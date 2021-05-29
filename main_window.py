import streamlit as st
import numpy as np

#st.header("ROI global:")


import pymc3 as pm
import matplotlib.pyplot as plt

textsize = 8

def simulate_beta_posterior(nb_trials, num_successes, beta_prior_a, beta_prior_b):
  posterior_draws = np.random.beta(num_successes+beta_prior_a,
  nb_trials-num_successes+beta_prior_b,
  10000
  )
  return posterior_draws

@st.cache
def get_funnel_posteriors(ads_cost, ads_nb_covers, ads_nb_clicks, nb_clients, prix_unitaire_produit, upsell_nb_ventes, prix_unitaire_upsell):
	posteriors_dict = {}
	CTR_posterior = simulate_beta_posterior(ads_nb_covers, ads_nb_clicks, 1, 1)
	page_visits_sample = ads_nb_covers*CTR_posterior
	posteriors_dict["CTR"] = CTR_posterior
	posteriors_dict["nb_visits_page"] = page_visits_sample

	CPC_posterior = ads_cost / page_visits_sample
	posteriors_dict["CPC"] = CPC_posterior

	conversion_rate_posterior = simulate_beta_posterior(ads_nb_clicks, nb_clients, 1, 1)
	posteriors_dict["page_conversion_rate"] = conversion_rate_posterior
	nb_clients_posterior = page_visits_sample*conversion_rate_posterior
	posteriors_dict["gains"] = prix_unitaire_produit*nb_clients_posterior

	upsell_conversion_rate = simulate_beta_posterior(nb_clients, upsell_nb_ventes, 1, 1)
	posteriors_dict["upsell_conversion_rate"] = upsell_conversion_rate
	posteriors_dict["upsell_gains"] = prix_unitaire_upsell*nb_clients_posterior*upsell_conversion_rate

	posteriors_dict["ROI"] = (posteriors_dict["gains"]+posteriors_dict["upsell_gains"])/ads_cost

	ROI_posterior = posteriors_dict["ROI"]
	proba_good_ROI = len(ROI_posterior[ROI_posterior>1]) / len(ROI_posterior) * 100

	return posteriors_dict, proba_good_ROI


def plot_funnel_posteriors(posteriors_dict, proba_good_ROI, textsize = 8):	
	fig1, axs = plt.subplots(2, 2)
	pm.plot_posterior(posteriors_dict["CTR"], hdi_prob=0.95, ax=axs[0,0], textsize=textsize)
	axs[0,0].set_title("CTR")
	pm.plot_posterior(posteriors_dict["CPC"], hdi_prob=0.95, ax=axs[0,1], textsize=textsize)
	axs[0,1].set_title("CPC")
	pm.plot_posterior(posteriors_dict["gains"], hdi_prob=0.95, ax=axs[1,0], textsize=textsize)
	axs[1,0].set_title("Gross sales - main product")
	pm.plot_posterior(posteriors_dict["upsell_gains"], hdi_prob=0.95, ax=axs[1,1], textsize=textsize)
	axs[1,1].set_title("Gross sales - Upsell product")
	fig1.tight_layout()
	st.pyplot(fig1)

	st.header("ROI global:")
	fig2, ax = plt.subplots()
	ax = pm.plot_posterior(posteriors_dict["ROI"], hdi_prob=0.95, ax=ax, textsize=textsize)
	ax.set_title("")
	st.pyplot(fig2)

	st.warning("La probabilié pour que le ROI soit supérieur à 1 est égale à : %.1f%%" % proba_good_ROI)


st.header("Data-Driven Web Marketing")

funnel_type = st.selectbox(
    'Choisir le type de  tunnel:',
     ["Publicité > Page de vente > Upsell"])


password = st.sidebar.text_input("Enter a password", type="password")
if password in st.secrets["PASSWORDS"]:

	st.sidebar.header("Compléter les information du tunnel")

	st.sidebar.subheader("1 - Publicité:")
	ads_cost = st.sidebar.number_input("Budget dépensé (€):", min_value=20, format="%.d")
	ads_nb_covers = st.sidebar.number_input("Nombre couvertures :", min_value=10, format="%.d")
	ads_nb_clicks = st.sidebar.number_input("Nombre de clicks uniques sortants:", min_value=10, format="%.d")

	st.sidebar.subheader("2 - Page de vente:")
	nb_clients = st.sidebar.number_input("Nombre de clients convertis par la page:", min_value=0, format="%.d")
	prix_unitaire_produit = st.sidebar.number_input("Prix unitaire du produit principal (€):", min_value=5, format="%.d")


	st.sidebar.subheader("3 - Upsell:")
	upsell_nb_ventes = st.sidebar.number_input("Nombre de clients ayant acheté l'upsell:", min_value=0, format="%.d")
	prix_unitaire_upsell = st.sidebar.number_input("Prix unitaire du produit Upsell (€):", min_value=20, format="%.d")

	posteriors_dict, proba_good_ROI = get_funnel_posteriors(ads_cost, ads_nb_covers, ads_nb_clicks, nb_clients, prix_unitaire_produit, upsell_nb_ventes, prix_unitaire_upsell)
	plot_funnel_posteriors(posteriors_dict, proba_good_ROI)

	st.subheader("What happens if we scale up ?")
	new_ads_cost = st.slider("New ads budget :", min_value=float(ads_cost), max_value=10.*ads_cost, step=ads_cost/10.)

	new_nb_clients = new_ads_cost/posteriors_dict["CPC"]*posteriors_dict["page_conversion_rate"]
	new_nb_upsells = new_nb_clients * posteriors_dict["upsell_conversion_rate"]
	margin_posterior = new_nb_clients*prix_unitaire_produit + new_nb_upsells*prix_unitaire_upsell - new_ads_cost
	fig3, ax = plt.subplots()
	ax = pm.plot_posterior(margin_posterior, hdi_prob=0.95, ax=ax, textsize=textsize)
	ax.set_title("Margin posterior if you scale")
	st.pyplot(fig3)
	proba_positive_margin = len(margin_posterior[margin_posterior>0]) / len(margin_posterior) * 100
	st.warning("The probability for having a positive margin is : %.1f%%" % proba_positive_margin)

#pm.forestplot(posteriors_dict, hdi_prob=0.95, ax=ax)
#ax.set_xscale('log')
#ax.set_title(" ")
#"""

