import { useState } from "react";

import SearchBar from "../components/SearchBar";
import ProductGrid from "../components/ProductGrid";

import { getRecommendations } from "../services/api";


function Recommendation() {

    const [products, setProducts] = useState([]);

    const [loading, setLoading] = useState(false);

    const [error, setError] = useState("");

    const [query, setQuery] = useState("");


    const handleSearch = async (searchQuery) => {

        setLoading(true);
        setError("");
        setQuery(searchQuery);

        try {

            const data = await getRecommendations(
                searchQuery,
                10
            );

            setProducts(
                data.results || []
            );

        } catch (err) {

            console.error(
                "Recommendation error:",
                err
            );

            setError(
                "Unable to get recommendations."
            );

            setProducts([]);

        } finally {

            setLoading(false);

        }
    };


    return (
        <div className="app">

            <header className="hero">

                <div className="hero-content">

                    <p className="tag">
                        AI-POWERED SHOPPING
                    </p>

                    <h1>
                        Multimodal E-Commerce Recommender
                    </h1>

                    <p>
                        Search for products using natural language.
                    </p>

                    <SearchBar
                        onSearch={handleSearch}
                        loading={loading}
                    />

                </div>

            </header>


            <main className="main-content">

                {query && (
                    <div className="results-header">

                        <h2>
                            Recommended Products
                        </h2>

                        <p>
                            Results for:
                            <strong> {query}</strong>
                        </p>

                    </div>
                )}


                {error && (
                    <div className="error-message">
                        {error}
                    </div>
                )}


                <ProductGrid
                    products={products}
                />

            </main>

        </div>
    );
}

export default Recommendation;