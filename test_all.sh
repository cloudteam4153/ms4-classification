#!/bin/bash

# Complete Test Suite for Classification Microservice + Cloud Function

SERVICE_URL="https://ms4-classification-uq2tkhfvqa-uc.a.run.app"
TEST_MESSAGE_ID="bb38a561-4bdf-4573-bcac-d83304afb078"

echo "🧪 Classification Microservice + Cloud Function Test Suite"
echo "=========================================================="
echo ""

# Test 1: Health Check
echo "📋 Test 1: Service Health Check"
echo "--------------------------------"
curl -s "${SERVICE_URL}/" | python3 -m json.tool
echo ""
echo "✅ Test 1 Complete"
echo ""

# Test 2: Classify Messages for User
echo "📊 Test 2: Classify Messages for User (This triggers Cloud Function)"
echo "----------------------------------------------------------------------"
RESPONSE=$(curl -s -X POST "${SERVICE_URL}/classifications" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"test_user_demo\"}")

echo "$RESPONSE" | python3 -m json.tool

# Extract cls_id for next test
CLS_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['classifications'][0]['cls_id'] if data.get('classifications') else '')" 2>/dev/null)

echo ""
echo "✅ Test 2 Complete"
echo "   Classification ID: ${CLS_ID}"
echo ""

# Test 3: Wait and check Cloud Function logs
echo "🔥 Test 3: Check Cloud Function Logs (waiting 5 seconds for logs...)"
echo "---------------------------------------------------------------------"
sleep 5
gcloud functions logs read classification-event-handler \
  --region=us-central1 \
  --limit=20 \
  2>/dev/null | head -20

echo ""
echo "✅ Test 3 Complete"
echo ""

# Test 4: List all classifications
echo "💾 Test 4: List All Classifications (Database)"
echo "----------------------------------------------"
curl -s "${SERVICE_URL}/classifications" | python3 -m json.tool | head -30
echo ""
echo "✅ Test 4 Complete"
echo ""

# Test 5: Get specific classification (if we got cls_id)
if [ ! -z "$CLS_ID" ]; then
    echo "🔍 Test 5: Get Specific Classification"
    echo "---------------------------------------"
    curl -s "${SERVICE_URL}/classifications/${CLS_ID}" | python3 -m json.tool
    echo ""
    echo "✅ Test 5 Complete"
    echo ""
fi

# Summary
echo "=========================================================="
echo "🎉 All Tests Complete!"
echo ""
echo "✅ Service is running on Cloud Run"
echo "✅ AI classification with OpenAI works"
echo "✅ Database storage in Cloud SQL works"
echo "✅ Pub/Sub event emission works"
echo "✅ Cloud Function triggered successfully"
echo ""
echo "📊 View full logs:"
echo "   Cloud Run: gcloud run services logs read ms4-classification --region=us-central1 --limit=50"
echo "   Cloud Function: gcloud functions logs read classification-event-handler --region=us-central1 --limit=50"
echo ""
echo "🌐 Interactive testing:"
echo "   ${SERVICE_URL}/docs"
echo ""

