from src.pipelines.pipeline import run_research_pipeline


def main():
    topic = "The impact of AI on the job market in 2026"

    result = run_research_pipeline(topic)

    print("\n" + "=" * 60)
    print("RESEARCH PIPELINE COMPLETED")
    print("=" * 60)

    print("\nFinal Report:")
    print(result["report"])

    print("\nCritic Feedback:")
    print(result["feedback"])


if __name__ == "__main__":
    main()