--
-- PostgreSQL database dump
--

\restrict 2OuA0cWX0IPWSegbJzbXxwjqtwv3fwXxvdSNgSNjYzkXEDpMcKNT2VUtQgeWckv

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

-- Started on 2026-09-28 18:32:28

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
-- TOC entry 221 (class 1259 OID 16608)
-- Name: movie_links; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.movie_links (
    movieid integer,
    imdbid integer,
    tmdbid integer
);


ALTER TABLE public.movie_links OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16598)
-- Name: movie_tags; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.movie_tags (
    movieid integer,
    tagid integer,
    relevance numeric
);


ALTER TABLE public.movie_tags OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 16611)
-- Name: movies; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.movies (
    movieid integer,
    title text,
    genres text
);


ALTER TABLE public.movies OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 16623)
-- Name: ratings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ratings (
    userid integer,
    movieid integer,
    rating numeric,
    "timestamp" timestamp without time zone
);


ALTER TABLE public.ratings OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 16603)
-- Name: tags; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tags (
    tagid integer,
    tag text
);


ALTER TABLE public.tags OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 16628)
-- Name: user_tags; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_tags (
    userid integer,
    movieid integer,
    tag text,
    "timestamp" timestamp without time zone
);


ALTER TABLE public.user_tags OWNER TO postgres;

-- Completed on 2026-09-28 18:32:28

--
-- PostgreSQL database dump complete
--

\unrestrict 2OuA0cWX0IPWSegbJzbXxwjqtwv3fwXxvdSNgSNjYzkXEDpMcKNT2VUtQgeWckv

