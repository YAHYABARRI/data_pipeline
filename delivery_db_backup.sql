--
-- PostgreSQL database dump
--

\restrict ckNpZKLbAEyDcT0HSITxWIOtxBBGYrqP8owUNvkbDwVkIyN7uw3TBIDiliRgLUe

-- Dumped from database version 18.6 (Debian 18.6-1.pgdg13+2)
-- Dumped by pg_dump version 18.6 (Debian 18.6-1.pgdg13+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: client; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client (
    id_client integer NOT NULL,
    nom character varying(100) NOT NULL,
    email character varying(150) NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.client OWNER TO postgres;

--
-- Name: client_id_client_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.client ALTER COLUMN id_client ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.client_id_client_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: commandes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.commandes (
    id_commande integer NOT NULL,
    id_client integer NOT NULL,
    id_restaurant integer NOT NULL,
    drivers_id integer,
    montant numeric(10,2) NOT NULL,
    statut character varying(30) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT commandes_montant_check CHECK ((montant >= (0)::numeric))
);


ALTER TABLE public.commandes OWNER TO postgres;

--
-- Name: commandes_id_commande_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.commandes ALTER COLUMN id_commande ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.commandes_id_commande_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: drivers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.drivers (
    drivers_id integer NOT NULL,
    nom character varying(100) NOT NULL,
    phone character varying(20) NOT NULL,
    is_available boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.drivers OWNER TO postgres;

--
-- Name: drivers_drivers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.drivers ALTER COLUMN drivers_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.drivers_drivers_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: order_summary; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.order_summary (
    id integer NOT NULL,
    nbr_commandes integer NOT NULL,
    somme numeric(10,2) NOT NULL,
    moyenne numeric(10,2) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.order_summary OWNER TO postgres;

--
-- Name: order_summary_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.order_summary ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.order_summary_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: restaurants; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.restaurants (
    id_restaurant integer NOT NULL,
    nom character varying(150) NOT NULL,
    city character varying(100) NOT NULL,
    category character varying(50),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.restaurants OWNER TO postgres;

--
-- Name: restaurants_id_restaurant_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.restaurants ALTER COLUMN id_restaurant ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.restaurants_id_restaurant_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Data for Name: client; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client (id_client, nom, email, created_at) FROM stdin;
1	Ahmed	ahmed.test@example.com	2026-11-08 16:59:36.45722
2	yassine	yassine@gmail.com	2026-11-08 16:59:36.462125
\.


--
-- Data for Name: commandes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.commandes (id_commande, id_client, id_restaurant, drivers_id, montant, statut, created_at) FROM stdin;
2	1	1	\N	25.50	en cours	2026-11-08 17:06:02.400968+00
1	1	1	\N	5.50	en cours	2026-11-08 16:59:36.468286+00
35	1	1	\N	25.50	en cours	2026-11-08 17:07:10.872539+00
3	1	1	\N	75.00	en cours	2026-11-08 17:06:45.121871+00
\.


--
-- Data for Name: drivers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.drivers (drivers_id, nom, phone, is_available, created_at) FROM stdin;
\.


--
-- Data for Name: order_summary; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.order_summary (id, nbr_commandes, somme, moyenne, created_at) FROM stdin;
1	4	131.50	32.88	2026-11-08 17:18:31.622966+00
2	4	131.50	32.88	2026-11-08 17:22:09.142508+00
3	4	131.50	32.88	2026-11-08 17:22:54.775568+00
\.


--
-- Data for Name: restaurants; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.restaurants (id_restaurant, nom, city, category, created_at) FROM stdin;
1	Pizza Express	Casablanca	Fast Food	2026-11-08 16:59:36.465018+00
2	Pizza Express	Casablanca	Fast Food	2026-11-08 17:06:02.397082+00
3	Pizza Express	Casablanca	Fast Food	2026-11-08 17:06:45.116906+00
35	Pizza Express	Casablanca	Fast Food	2026-11-08 17:07:10.869887+00
\.


--
-- Name: client_id_client_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.client_id_client_seq', 68, true);


--
-- Name: commandes_id_commande_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.commandes_id_commande_seq', 67, true);


--
-- Name: drivers_drivers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.drivers_drivers_id_seq', 1, false);


--
-- Name: order_summary_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.order_summary_id_seq', 3, true);


--
-- Name: restaurants_id_restaurant_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.restaurants_id_restaurant_seq', 67, true);


--
-- Name: client client_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client
    ADD CONSTRAINT client_email_key UNIQUE (email);


--
-- Name: client client_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client
    ADD CONSTRAINT client_pkey PRIMARY KEY (id_client);


--
-- Name: commandes commandes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.commandes
    ADD CONSTRAINT commandes_pkey PRIMARY KEY (id_commande);


--
-- Name: drivers drivers_phone_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.drivers
    ADD CONSTRAINT drivers_phone_key UNIQUE (phone);


--
-- Name: drivers drivers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.drivers
    ADD CONSTRAINT drivers_pkey PRIMARY KEY (drivers_id);


--
-- Name: order_summary order_summary_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.order_summary
    ADD CONSTRAINT order_summary_pkey PRIMARY KEY (id);


--
-- Name: restaurants restaurants_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_pkey PRIMARY KEY (id_restaurant);


--
-- Name: commandes commandes_drivers_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.commandes
    ADD CONSTRAINT commandes_drivers_id_fkey FOREIGN KEY (drivers_id) REFERENCES public.drivers(drivers_id);


--
-- Name: commandes commandes_id_client_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.commandes
    ADD CONSTRAINT commandes_id_client_fkey FOREIGN KEY (id_client) REFERENCES public.client(id_client);


--
-- Name: commandes commandes_id_restaurant_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.commandes
    ADD CONSTRAINT commandes_id_restaurant_fkey FOREIGN KEY (id_restaurant) REFERENCES public.restaurants(id_restaurant);


--
-- PostgreSQL database dump complete
--

\unrestrict ckNpZKLbAEyDcT0HSITxWIOtxBBGYrqP8owUNvkbDwVkIyN7uw3TBIDiliRgLUe

