export default function Disclaimer() {
    return <div className="bg-red-600 text-center text-white text-sm md:text-xl p-2 space-y-2">
        <p className="font-bold pb-4">Disclaimer:</p>
        <p>This website and it’s contents are a proof of concept only. </p>
        <p>The danger levels and forecast discussions are entirely AI-generated.</p>
        <p>The forecasts and data shown should never be used to make decisions when traveling in the backcountry.</p>
        <p>For an accurate forecast made by professionals, visit</p>
        <a
            href="https://flatheadavalanche.com"
            target="_blank"
            rel="noopener noreferrer"
            className="font-bold hover:underline"
        >
            flatheadavalanche.com
        </a>
    </div>
}