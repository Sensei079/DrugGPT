export interface DrugInfo {
    name: string;
    info: string;
    side_effects: string;
    warnings: string;
}

export interface DrugResponse {
    drugs: DrugInfo[];
    safe: boolean;
}

export interface DrugQuery {
    drugs: string[];
} 