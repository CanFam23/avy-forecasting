export default function Disclaimer() {
    return (
        <div className="bg-red-600 text-center text-white text-sm md:text-xl p-2 space-y-2">
            <p className="font-bold pb-4">Disclaimer:</p>
            <p>This website and its contents are provided for proof-of-concept purposes only.</p>
            <p>The danger levels and forecast discussions are entirely AI-generated.</p>
            <p>The forecasts and data displayed must not be used for decision-making in the backcountry.</p>
            <p>For official forecasts prepared by professionals, please visit:</p>
            <a
                href="https://flatheadavalanche.com"
                target="_blank"
                rel="noopener noreferrer"
                className="font-bold hover:underline"
            >
                flatheadavalanche.com
            </a>
        </div>
    );
}