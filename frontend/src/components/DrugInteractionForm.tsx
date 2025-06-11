import React, { useState } from 'react';
import {
    Box,
    Button,
    Textarea,
    VStack,
    Text,
    useToast,
    Alert,
    AlertIcon,
    AlertTitle,
    AlertDescription,
    Card,
    CardBody,
    Heading,
    Select,
} from '@chakra-ui/react';

interface DrugInfo {
    name: string;
    info: string;
    side_effects: string;
    warnings: string;
    precautions: string;
    is_safe: boolean;
}

interface DrugResponse {
    drugs: DrugInfo[];
    safe: boolean;
    interaction_message: string;
    friendly_response: string;
}

const QUERY_TYPES = [
    { value: 'interaction', label: 'Drug Interactions' },
    { value: 'side_effects', label: 'Side Effects' },
    { value: 'precautions', label: 'Precautions' },
    { value: 'info', label: 'General Information' },
];

const DrugInteractionForm: React.FC = () => {
    const [query, setQuery] = useState('');
    const [queryType, setQueryType] = useState('interaction');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<DrugResponse | null>(null);
    const toast = useToast();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await fetch('http://localhost:8000/check-interactions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    query_type: queryType
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to check drug information');
            }

            const data = await response.json();
            setResult(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
            toast({
                title: 'Error',
                description: err instanceof Error ? err.message : 'An error occurred',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setLoading(false);
        }
    };

    const getPlaceholder = () => {
        switch (queryType) {
            case 'side_effects':
                return 'Example: What are the side effects of ibuprofen?';
            case 'precautions':
                return 'Example: What precautions should I take with amoxicillin?';
            case 'info':
                return 'Example: Tell me about metformin';
            default:
                return 'Example: I have a headache but took aspirin this morning - can I take Tylenol?';
        }
    };

    return (
        <Box maxW="600px" mx="auto" p={4}>
            <Card>
                <CardBody>
                    <VStack spacing={4} align="stretch">
                        <Heading size="md">Drug Information Assistant</Heading>

                        <Text>
                            Ask about drug interactions, side effects, precautions, or general information.
                            You can use natural language to describe your situation.
                        </Text>

                        <form onSubmit={handleSubmit}>
                            <VStack spacing={4}>
                                <Select
                                    value={queryType}
                                    onChange={(e) => setQueryType(e.target.value)}
                                    size="lg"
                                >
                                    {QUERY_TYPES.map(type => (
                                        <option key={type.value} value={type.value}>
                                            {type.label}
                                        </option>
                                    ))}
                                </Select>

                                <Textarea
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    placeholder={getPlaceholder()}
                                    size="lg"
                                    rows={3}
                                />

                                <Button
                                    type="submit"
                                    colorScheme="blue"
                                    isLoading={loading}
                                    loadingText="Checking..."
                                    isDisabled={!query.trim()}
                                    width="100%"
                                >
                                    Get Information
                                </Button>
                            </VStack>
                        </form>

                        {error && (
                            <Alert status="error">
                                <AlertIcon />
                                <AlertTitle>Error!</AlertTitle>
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}

                        {result && (
                            <VStack spacing={4} align="stretch">
                                <Alert status={result.safe ? "success" : "warning"}>
                                    <AlertIcon />
                                    {result.friendly_response}
                                </Alert>

                                {result.drugs.map((drug, index) => (
                                    <Card key={index} variant="outline">
                                        <CardBody>
                                            <VStack align="stretch" spacing={2}>
                                                <Heading size="sm">{drug.name}</Heading>
                                                <Text>{drug.info}</Text>
                                                {drug.warnings && (
                                                    <Alert status="warning">
                                                        <AlertIcon />
                                                        {drug.warnings}
                                                    </Alert>
                                                )}
                                                {drug.side_effects && (
                                                    <Text color="gray.600">
                                                        Side Effects: {drug.side_effects}
                                                    </Text>
                                                )}
                                                {drug.precautions && (
                                                    <Text color="blue.600">
                                                        Precautions: {drug.precautions}
                                                    </Text>
                                                )}
                                            </VStack>
                                        </CardBody>
                                    </Card>
                                ))}
                            </VStack>
                        )}
                    </VStack>
                </CardBody>
            </Card>
        </Box>
    );
};

export default DrugInteractionForm; 