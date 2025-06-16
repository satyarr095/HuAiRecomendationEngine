import { useState, useRef, type ChangeEvent, type KeyboardEvent } from "react";
import { CheckCircle2, UploadCloud, AlertCircle, Sparkles, Database, Shield } from "lucide-react";
import { motion } from "framer-motion";
import './LandingPage.css';

export default function LandingPage() {
    const [jsonData, setJsonData] = useState<Record<string, unknown> | null>(null);
    const [error, setError] = useState<string>("");
    const [fileName, setFileName] = useState<string>("");
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsLoading(true);
        setError("");

        try {
            if (file.type !== "application/json" && !file.name.endsWith('.json')) {
                throw new Error("Please upload a valid JSON file");
            }

            // Check file size (max 10MB)
            if (file.size > 10 * 1024 * 1024) {
                throw new Error("File size must be less than 10MB");
            }

            const reader = new FileReader();
            reader.onload = (event: ProgressEvent<FileReader>) => {
                try {
                    const result = event.target?.result as string;
                    if (!result) {
                        throw new Error("Failed to read file");
                    }

                    const parsed = JSON.parse(result);
                    setJsonData(parsed);
                    setFileName(file.name);
                    setError("");
                } catch (parseError) {
                    setError("Invalid JSON format. Please check your file and try again.");
                    setJsonData(null);
                    setFileName("");
                } finally {
                    setIsLoading(false);
                }
            };

            reader.onerror = () => {
                setError("Failed to read file. Please try again.");
                setIsLoading(false);
            };

            reader.readAsText(file);
        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred");
            setIsLoading(false);
        }
    };

    const handleContinue = () => {
        if (jsonData) {
            // Handle continue logic here
            console.log("Continue with data:", jsonData);
        }
    };

    const handleKeyPress = (e: KeyboardEvent<HTMLDivElement>) => {
        if (e.key === 'Enter' || e.key === ' ') {
            fileInputRef.current?.click();
        }
    };

    const resetUpload = () => {
        setJsonData(null);
        setError("");
        setFileName("");
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    const features = [
        {
            icon: Sparkles,
            title: "AI-Powered Analysis",
            description: "Advanced algorithms analyze your data patterns"
        },
        {
            icon: Shield,
            title: "Secure Processing",
            description: "Enterprise-grade security for your sensitive data"
        },
        {
            icon: Database,
            title: "Smart Insights",
            description: "Get actionable recommendations instantly"
        }
    ];

    return (
        <div className="landing-container">
            {/* Floating elements for visual interest */}
            <div className="floating-elements">
                <div className="floating-orb orb-1"></div>
                <div className="floating-orb orb-2"></div>
                <div className="floating-orb orb-3"></div>
            </div>

            {/* Hero Section */}
            <section className="hero-section">
                <div className="container">
                    <motion.div
                        initial={{ opacity: 0, y: 40 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                        className="hero-content"
                    >
                        <div className="badge">
                            <Sparkles className="badge-icon" />
                            <span>Next-Generation AI Engine</span>
                        </div>

                        <h1 className="hero-title">
                            Transform Your Data Into
                            <span className="gradient-text"> Intelligent Insights</span>
                        </h1>

                        <p className="hero-subtitle">
                            Upload your JSON data and let our advanced AI recommendation engine 
                            discover patterns, trends, and opportunities you never knew existed.
                        </p>
                    </motion.div>

                    {/* Upload Section */}
                    <motion.div
                        initial={{ opacity: 0, y: 40 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
                        className="upload-section"
                    >
                        <div className="upload-card">
                            <div className="upload-header">
                                <UploadCloud className="upload-icon" />
                                <h3 className="upload-title">Upload Your Data</h3>
                                <p className="upload-description">
                                    Drag and drop your JSON file or click to browse
                                </p>
                            </div>

                            <div
                                className="upload-zone"
                                role="button"
                                tabIndex={0}
                                onKeyDown={handleKeyPress}
                                aria-label="Click to upload JSON file"
                            >
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".json,application/json"
                                    onChange={handleFileUpload}
                                    className="file-input"
                                    disabled={isLoading}
                                    aria-describedby={error ? "error-message" : undefined}
                                />
                                
                                <div className="upload-content">
                                    <div className="upload-visual">
                                        <div className="upload-circle">
                                            <UploadCloud />
                                        </div>
                                    </div>
                                    <div className="upload-text">
                                        <p className="upload-primary">Choose a JSON file</p>
                                        <p className="upload-secondary">or drag it here</p>
                                        <p className="upload-limit">Maximum file size: 10MB</p>
                                    </div>
                                </div>
                            </div>

                            {error && (
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    id="error-message"
                                    className="status-message error"
                                    role="alert"
                                    aria-live="polite"
                                >
                                    <AlertCircle className="status-icon" />
                                    <span>{error}</span>
                                </motion.div>
                            )}

                            {jsonData && fileName && (
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="status-message success"
                                    role="status"
                                    aria-live="polite"
                                >
                                    <CheckCircle2 className="status-icon" />
                                    <span>
                                        <strong>{fileName}</strong> uploaded successfully!
                                    </span>
                                </motion.div>
                            )}

                            <div className="upload-actions">
                                {jsonData && (
                                    <button
                                        onClick={resetUpload}
                                        className="btn btn-secondary"
                                        type="button"
                                    >
                                        Upload New File
                                    </button>
                                )}

                                <button
                                    onClick={handleContinue}
                                    disabled={!jsonData || isLoading}
                                    className={`btn btn-primary ${isLoading ? 'loading' : ''}`}
                                    type="button"
                                >
                                    {isLoading ? (
                                        <>
                                            <div className="spinner"></div>
                                            Processing...
                                        </>
                                    ) : (
                                        <>
                                            Continue
                                            <span className="btn-arrow">→</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Features Section */}
            <motion.section
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.8, delay: 0.4 }}
                className="features-section"
            >
                <div className="container">
                    <div className="features-grid">
                        {features.map((feature, index) => (
                            <motion.div
                                key={feature.title}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.6, delay: 0.6 + index * 0.1 }}
                                className="feature-card"
                            >
                                <div className="feature-icon">
                                    <feature.icon />
                                </div>
                                <h3 className="feature-title">{feature.title}</h3>
                                <p className="feature-description">{feature.description}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </motion.section>

            {/* Trust Section */}
            <motion.section
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.8, delay: 0.8 }}
                className="trust-section"
            >
                <div className="container">
                    <p className="trust-text">
                        <Shield className="trust-icon" />
                        Your data is processed securely and never stored on our servers
                    </p>
                </div>
            </motion.section>
        </div>
    );
}